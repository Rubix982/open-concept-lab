package main

import (
	"bufio"
	"compress/gzip"
	"encoding/xml"
	"fmt"
	"html"
	"io"
	"os"
	"path/filepath"
	"regexp"
	"sort"
	"strings"
	"time"

	colly "github.com/gocolly/colly/v2"
	"github.com/lib/pq"
)

// The DBLP XML dump (https://dblp.org/xml/dblp.xml.gz, ~1.1 GB, monthly). The DBLP API is
// rate-limited and bot-guarded, so the explorer reads papers from this dump instead.
const (
	dblpDumpFile           = "dblp/dblp.xml.gz"
	dblpRecentYears        = 6
	dblpMaxPapersPerPerson = 30
)

var dblpTagRegex = regexp.MustCompile(`<[^>]+>`)

type dblpRecord struct {
	Key     string   `xml:"key,attr"`
	Authors []string `xml:"author"`
	Title   struct {
		Inner string `xml:",innerxml"`
	} `xml:"title"`
	Year      int      `xml:"year"`
	Booktitle string   `xml:"booktitle"`
	Journal   string   `xml:"journal"`
	EE        []string `xml:"ee"`
}

// dblpPerson is a person record (<www key="homepages/...">): all their name spellings and their
// current and former affiliations.
type dblpPerson struct {
	Key     string   `xml:"key,attr"`
	Authors []string `xml:"author"`
	Notes   []struct {
		Type  string `xml:"type,attr"`
		Label string `xml:"label,attr"`
		Text  string `xml:",chardata"`
	} `xml:"note"`
}

type dblpAffiliation struct {
	name, affiliation string
	former            bool
}

type dblpRow struct {
	key, title, venue, url string
	year                   int
}

// latin1Reader decodes ISO-8859-1 (dblp.xml's declared encoding) into UTF-8.
type latin1Reader struct{ r *bufio.Reader }

func (l latin1Reader) Read(p []byte) (int, error) {
	n := 0
	for n+1 < len(p) {
		b, err := l.r.ReadByte()
		if err != nil {
			return n, err
		}
		if b < 0x80 {
			p[n] = b
			n++
		} else {
			p[n], p[n+1] = 0xC0|b>>6, 0x80|b&0x3F
			n += 2
		}
	}
	return n, nil
}

// loadDblpPapers keeps, for every CSRankings professor, their papers from the last few years
// (journal articles, conference papers, book chapters), newest first, capped per person.
func loadDblpPapers(mainCtx *colly.Context) error {
	path := filepath.Join(getRootDirPath(DATA_DIR), dblpDumpFile)
	f, err := os.Open(path)
	if os.IsNotExist(err) {
		logger.Warnf(mainCtx, "⚠️ %s not found; skipping DBLP papers (download https://dblp.org/xml/dblp.xml.gz)", path)
		return nil
	}
	if err != nil {
		return fmt.Errorf("failed to open %s: %w", path, err)
	}
	defer f.Close()

	db, err := GetDB()
	if err != nil {
		return fmt.Errorf("cannot get DB: %w", err)
	}

	names := map[string]bool{}
	// OpenAlex researchers (other fields) are not looked up in DBLP: a same-name computer scientist
	// would lend them their papers.
	rows, err := db.Query(`SELECT name FROM professors WHERE source = 'csrankings'`)
	if err != nil {
		return fmt.Errorf("failed to load professor names: %w", err)
	}
	for rows.Next() {
		var n string
		if err := rows.Scan(&n); err != nil {
			rows.Close()
			return err
		}
		names[n] = true
	}
	rows.Close()

	gz, err := gzip.NewReader(bufio.NewReaderSize(f, 1<<20))
	if err != nil {
		return fmt.Errorf("failed to read %s: %w", path, err)
	}
	dec := xml.NewDecoder(bufio.NewReaderSize(gz, 1<<20))
	dec.Strict = false
	dec.Entity = xml.HTMLEntity
	dec.CharsetReader = func(label string, input io.Reader) (io.Reader, error) {
		if strings.EqualFold(label, "ISO-8859-1") {
			return latin1Reader{bufio.NewReader(input)}, nil
		}
		return nil, fmt.Errorf("unsupported charset %q", label)
	}

	minYear := time.Now().Year() - dblpRecentYears
	papers := map[string][]dblpRow{}
	var affiliations []dblpAffiliation
	records := 0
	for {
		tok, err := dec.Token()
		if err == io.EOF {
			break
		}
		if err != nil {
			return fmt.Errorf("failed to parse DBLP dump: %w", err)
		}
		se, ok := tok.(xml.StartElement)
		if !ok {
			continue
		}
		switch se.Name.Local {
		case "article", "inproceedings", "incollection":
		case "www":
			// Person records: keep the affiliations of CSRankings people, under each of their names.
			var p dblpPerson
			if err := dec.DecodeElement(&p, &se); err != nil {
				return fmt.Errorf("failed to parse DBLP person record: %w", err)
			}
			if !strings.HasPrefix(p.Key, "homepages/") {
				continue
			}
			for _, a := range p.Authors {
				if !names[a] {
					continue
				}
				for _, n := range p.Notes {
					if n.Type == "affiliation" && strings.TrimSpace(n.Text) != "" {
						affiliations = append(affiliations, dblpAffiliation{a, strings.TrimSpace(html.UnescapeString(n.Text)), n.Label == "former"})
					}
				}
			}
			continue
		case "dblp":
			continue
		default:
			if err := dec.Skip(); err != nil {
				return fmt.Errorf("failed to parse DBLP dump: %w", err)
			}
			continue
		}

		var rec dblpRecord
		if err := dec.DecodeElement(&rec, &se); err != nil {
			return fmt.Errorf("failed to parse DBLP record: %w", err)
		}
		records++
		if rec.Year < minYear {
			continue
		}
		title := strings.TrimSuffix(strings.TrimSpace(html.UnescapeString(dblpTagRegex.ReplaceAllString(rec.Title.Inner, ""))), ".")
		if title == "" {
			continue
		}
		row := dblpRow{key: rec.Key, title: title, year: rec.Year, venue: rec.Booktitle}
		if row.venue == "" {
			row.venue = rec.Journal
		}
		if len(rec.EE) > 0 {
			row.url = rec.EE[0]
		}
		for _, a := range rec.Authors {
			if names[a] {
				papers[a] = append(papers[a], row)
			}
		}
	}

	tx, err := db.Begin()
	if err != nil {
		return fmt.Errorf("failed to begin transaction: %w", err)
	}
	defer tx.Rollback()
	if _, err := tx.Exec(`TRUNCATE dblp_papers`); err != nil {
		return fmt.Errorf("failed to clear dblp_papers: %w", err)
	}
	stmt, err := tx.Prepare(pq.CopyIn("dblp_papers", "name", "dblp_key", "title", "venue", "year", "url"))
	if err != nil {
		return fmt.Errorf("failed to start COPY: %w", err)
	}
	kept := 0
	for name, list := range papers {
		sort.Slice(list, func(i, j int) bool {
			if list[i].year != list[j].year {
				return list[i].year > list[j].year
			}
			return list[i].key > list[j].key
		})
		seen := map[string]bool{}
		for _, p := range list {
			if len(seen) >= dblpMaxPapersPerPerson {
				break
			}
			if seen[p.key] {
				continue
			}
			seen[p.key] = true
			if _, err := stmt.Exec(name, p.key, p.title, nullIfEmpty(p.venue), p.year, nullIfEmpty(p.url)); err != nil {
				return fmt.Errorf("failed to COPY paper: %w", err)
			}
			kept++
		}
	}
	if _, err := stmt.Exec(); err != nil {
		return fmt.Errorf("failed to flush COPY: %w", err)
	}
	if err := stmt.Close(); err != nil {
		return fmt.Errorf("failed to close COPY: %w", err)
	}
	if _, err := tx.Exec(`TRUNCATE dblp_affiliations`); err != nil {
		return fmt.Errorf("failed to clear dblp_affiliations: %w", err)
	}
	astmt, err := tx.Prepare(pq.CopyIn("dblp_affiliations", "name", "affiliation", "former"))
	if err != nil {
		return fmt.Errorf("failed to start COPY: %w", err)
	}
	for _, a := range affiliations {
		if _, err := astmt.Exec(a.name, a.affiliation, a.former); err != nil {
			return fmt.Errorf("failed to COPY affiliation: %w", err)
		}
	}
	if _, err := astmt.Exec(); err != nil {
		return fmt.Errorf("failed to flush COPY: %w", err)
	}
	if err := astmt.Close(); err != nil {
		return fmt.Errorf("failed to close COPY: %w", err)
	}
	if err := tx.Commit(); err != nil {
		return fmt.Errorf("failed to commit DBLP papers: %w", err)
	}

	logger.Infof(mainCtx, "📄 DBLP: read %d records; kept %d papers (%d+) for %d CSRankings faculty; %d affiliations",
		records, kept, minYear, len(papers), len(affiliations))
	return nil
}
