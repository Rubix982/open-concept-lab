package main

// Approximate US-dollar values, so amounts from 42 funders can be compared at a glance. Fixed rates
// (mid-2026, rounded), not live: the page labels them "approximately". A currency missing here has
// no dollar value and the page shows only the original amount.
var usdPerUnit = map[string]float64{
	"USD": 1, "EUR": 1.08, "GBP": 1.27, "JPY": 0.0067, "CAD": 0.73, "AUD": 0.66, "CHF": 1.13,
	"NZD": 0.60, "HKD": 0.128, "CNY": 0.14, "TWD": 0.031, "BRL": 0.18, "KRW": 0.00073, "SEK": 0.095,
	"NOK": 0.093, "DKK": 0.145, "PLN": 0.25, "ILS": 0.27, "INR": 0.012, "CLP": 0.0011, "VND": 0.00004,
	"LKR": 0.0033, "PKR": 0.0036, "CZK": 0.044, "TRY": 0.029,
}

// usd converts an amount to approximate US dollars; nil when the amount or the rate is unknown.
func usd(amount *float64, currency *string) *float64 {
	if amount == nil || currency == nil {
		return nil
	}
	rate, ok := usdPerUnit[*currency]
	if !ok {
		return nil
	}
	v := *amount * rate
	return &v
}
