use reqwest::blocking::get;
use scraper::{Html, Selector};
use serde_json;
use std::collections::HashMap;
use std::fs::File;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let body = get("https://arxiv.org/category_taxonomy")?.text()?;
    let document = Html::parse_document(&body);
    let header_selector = Selector::parse(".accordion-head").unwrap();
    let body_selector = Selector::parse(".accordion-body").unwrap();

    let header_elems = document.select(&header_selector);
    let body_elems = document.select(&body_selector);

    let mut data: HashMap<String, Vec<HashMap<String, HashMap<String, String>>>> = HashMap::new();

    for (head, body) in header_elems.zip(body_elems) {
        let categories_against_desc = Selector::parse(".columns.divided").unwrap();
        let inner_div_selector = Selector::parse("div").unwrap();
        let h4_selector = Selector::parse("h4").unwrap();
        let p_selector = Selector::parse("p").unwrap();
        let span_selector = Selector::parse("span").unwrap();

        for container in body.select(&categories_against_desc) {
            let mut abbr_text = String::new();
            let mut name = String::new();
            let mut description = String::new();
            let mut entry = HashMap::new();

            for (i, inner_container) in container.select(&inner_div_selector).enumerate() {
                if i == 0 {
                    for t in inner_container.select(&h4_selector) {
                        let title_text = t.inner_html();
                        match title_text.find(' ') {
                            Some(index) => {
                                abbr_text = title_text[..index].to_string();
                            }
                            None => {
                                abbr_text = title_text.to_string();
                            }
                        };
                    }
                    for s in inner_container.select(&span_selector) {
                        name = s
                            .inner_html()
                            .strip_prefix('(')
                            .unwrap()
                            .strip_suffix(')')
                            .unwrap()
                            .to_string();
                    }
                } else {
                    for p in inner_container.select(&p_selector) {
                        description = p.inner_html();
                    }
                }
            }

            let mut inner_data = HashMap::new();
            inner_data.insert("name".to_string(), name);
            inner_data.insert("description".to_string(), description);
            entry.insert(abbr_text, inner_data);
            data.entry(head.inner_html().to_string())
                .or_insert(Vec::new())
                .push(entry);
        }
    }

    // Output is available at this gist: https://gist.github.com/Rubix982/e0eb6c035829d9691002466e02bfabaf
    let file = File::create("out/arxiv_categories.json")?;
    serde_json::to_writer_pretty(file, &data).expect("Failed to write to file");

    Ok(())
}
