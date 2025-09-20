package main

import (
	"net/http"
)

// http://export.arxiv.org/api/query?search_query=<query>&start=<start>&max_results=<max_results>&sortBy=<sort_field>&sortOrder=<asc|desc>
// http://export.arxiv.org/api/query?search_query=cat:cs.AI&start=0&max_results=1000&sortBy=submittedDate&sortOrder=ascending
/* Parameters

Parameter	Description
search_query	Query string (category, author, keyword, etc.), e.g., cat:cs.AI
start	0-based index for pagination
max_results	Max 2000 (practical: 100-1000)
sortBy	submittedDate, lastUpdatedDate, or relevance
sortOrder	ascending or descending
*/
func main() {
	http.Get()
}
