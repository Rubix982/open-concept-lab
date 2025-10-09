package main

import (
	"fmt"
	"strings"
)

func prettyPrintRows(rows map[string][]string) {
	fmt.Println("=== Rows ===")
	for key, vals := range rows {
		fmt.Printf("%-20s -> %s\n", key, strings.Join(vals, ", "))
	}
	fmt.Println("====================")
}
