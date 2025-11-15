from bs4 import BeautifulSoup

with open("usnews_top_universities.html", "r", encoding="utf-8") as f:
    html_content = f.read()

soup = BeautifulSoup(html_content, "html.parser")

ol_tag = soup.find("ol")
li_tags = ol_tag.find_all("li") if ol_tag else []
all_universities = []

for index, li in enumerate(li_tags, start=1):  # type: ignore
    for h3_tag in li.find_all("h3"):
        # Get all text, including from nested tags, separated by spaces
        all_universities.append(f"('{" ".join(h3_tag.stripped_strings)}')")

sql_query = f"""
WITH input_list(name) AS (
  VALUES
    {',\n    '.join(all_universities)}
)
SELECT name
FROM input_list
WHERE NOT EXISTS (
  SELECT 1
  FROM universities u
  WHERE u.institution = input_list.name
);
"""
print(sql_query)
