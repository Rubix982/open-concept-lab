package cacherouter

import "testing"

func byPolicy(t *testing.T) map[string]Stats {
	t.Helper()
	out, err := Run(nil)
	if err != nil {
		t.Fatal(err)
	}
	m := map[string]Stats{}
	for _, s := range out.(Result).Stats {
		m[s.Policy] = s
	}
	return m
}

// The page's claims, at the default settings.
func TestAffinityKeepsPrefixesCached(t *testing.T) {
	s := byPolicy(t)
	if s["round-robin"].HitRate > 0.6 || s["affinity"].HitRate < 0.9 {
		t.Fatalf("hit rates: round robin %.2f, affinity %.2f", s["round-robin"].HitRate, s["affinity"].HitRate)
	}
	if s["affinity"].TTFTP50*5 > s["round-robin"].TTFTP50 {
		t.Fatalf("affinity p50 %.3fs not 5x better than round robin %.3fs", s["affinity"].TTFTP50, s["round-robin"].TTFTP50)
	}
}

func TestLoadCapSpreadsTheHotPrefix(t *testing.T) {
	s := byPolicy(t)
	if s["bounded"].MaxBusy >= s["affinity"].MaxBusy {
		t.Fatalf("busiest server: bounded %.2f, affinity %.2f", s["bounded"].MaxBusy, s["affinity"].MaxBusy)
	}
	if s["bounded"].TTFTP99 > s["affinity"].TTFTP99 {
		t.Fatalf("p99: bounded %.3fs, affinity %.3fs", s["bounded"].TTFTP99, s["affinity"].TTFTP99)
	}
	if s["bounded"].HitRate < 0.9 {
		t.Fatalf("bounded hit rate %.2f", s["bounded"].HitRate)
	}
}

func TestSameWorkloadForEveryPolicy(t *testing.T) {
	p := Defaults()
	_, a := workload(p)
	_, b := workload(p)
	if len(a) != len(b) || a[10] != b[10] {
		t.Fatal("workload is not deterministic")
	}
}

func TestCacheNeverOverfills(t *testing.T) {
	c := &lru{cap: 5000, size: map[int]int{}}
	for i := 0; i < 50; i++ {
		c.insert(i, 1500+i*37%2000)
		if c.used > c.cap {
			t.Fatalf("used %d > cap %d", c.used, c.cap)
		}
	}
}
