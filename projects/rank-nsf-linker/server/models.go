package main

type University struct {
	ID          string  `json:"id" db:"id"`
	Name        string  `json:"name" db:"name"`
	CountryCode string  `json:"country_code" db:"country_code"`
	Latitude    float64 `json:"latitude" db:"latitude"`
	Longitude   float64 `json:"longitude" db:"longitude"`
	Region      string  `json:"region" db:"region"`
	CountryName string  `json:"country_name" db:"country_name"`
}

type Professor struct {
	Name          string  `json:"name" db:"name"`
	AffiliationID string  `json:"affiliation_id" db:"affiliation_id"`
	Homepage      string  `json:"homepage" db:"homepage"`
	ScholarID     string  `json:"scholar_id" db:"scholar_id"`
	Departments   string  `json:"departments" db:"departments"`
	ResearchArea  string  `json:"research_area" db:"research_area"`
	PaperCount    float64 `json:"paper_count" db:"paper_count"`
	AdjustedCount float64 `json:"adjusted_count" db:"adjusted_count"`
	Year          int     `json:"year" db:"year"`
}

type NsfAward struct {
	AwardID                                string  `json:"awd_id" db:"awd_id"`
	AgencyId                               string  `json:"agcy_id" db:"agcy_id"`
	TransactionType                        string  `json:"tran_type" db:"tran_type"`
	AwardInstrumentText                    string  `json:"awd_istr_txt" db:"awd_istr_txt"`
	AwardTitleText                         string  `json:"awd_titl_txt" db:"awd_titl_txt"`
	FederalCatalogDomesticAssistanceNumber string  `json:"cfda_num" db:"cfda_num"`
	OrgCode                                string  `json:"org_code" db:"org_code"`
	ProgramOfficePhoneNumber               string  `json:"po_phone" db:"po_phone"`
	ProgramOfficeEmailNumber               string  `json:"po_email" db:"po_email"`
	NSFSigningOfficer                      string  `json:"po_sign_block_name" db:"po_sign_block_name"`
	AwardEffectiveDate                     string  `json:"awd_eff_date" db:"awd_eff_date"`
	AwardExpiryDate                        string  `json:"awd_exp_date" db:"awd_exp_date"`
	TotalIntendedAwardAmount               float64 `json:"tot_intn_awd_amt" db:"tot_intn_awd_amt"`
	ActualAwardAmount                      float64 `json:"awd_amount" db:"awd_amount"`
	EarliestAmendmentDate                  string  `json:"awd_min_amd_letter_date" db:"awd_min_amd_letter_date"`
	MostRecentAmendmentDate                string  `json:"awd_max_amd_letter_date" db:"awd_max_amd_letter_date"`
	AwardAbstract                          string  `json:"awd_abstract_narration" db:"awd_abstract_narration"`

	// Amount from the American Recovery and Reinvestment Act (ARAA), if applicable
	AwardARRA float64 `json:"awd_arra_amount" db:"awd_arra_amount"`

	DirectorateAbbreviation string `json:"dir_abbr" db:"dir_abbr"`
	FullDirectorateName     string `json:"org_div_long_name" db:"org_div_long_name"`
	AwardingAgencyCode      string `json:"awd_agcy_code" db:"awd_agcy_code"`
	FundingAgencyCode       string `json:"fund_agcy_code" db:"fund_agcy_code"`
	PrincipalInvestigors    []struct {
		Role       string `json:"pi_role" db:"pi_role"`
		FirstName  string `json:"pi_first_name" db:"pi_first_name"`
		LastName   string `json:"pi_last_name" db:"pi_last_name"`
		MiddleName string `json:"pi_mid_init" db:"pi_mid_init"`
		NameSuffix string `json:"pi_sufx_name" db:"pi_sufx_name"`
		EmailAddr  string `json:"pi_email_addr" db:"pi_email_addr"`
		NSFId      string `json:"nsf_id" db:"nsf_id"`
		StartDate  string `json:"pi_start_date" db:"pi_start_date"`
		EndDate    string `json:"pi_end_date" db:"pi_end_date"`
	} `json:"pi" db:"pi"`
	Institute struct {
		Name                       string `json:"inst_name" db:"inst_name"`
		StreetAddress              string `json:"inst_street_address" db:"inst_street_address"`
		StreetAddressV2            string `json:"inst_street_address_2" db:"inst_street_address_2"`
		City                       string `json:"inst_city_name" db:"inst_city_name"`
		StateCode                  string `json:"inst_state_code" db:"inst_state_code"`
		StateName                  string `json:"inst_state_name" db:"inst_state_name"`
		PhoneNumber                string `json:"inst_phone_num" db:"inst_phone_num"`
		ZipCode                    string `json:"inst_zip_code" db:"inst_zip_code"`
		Country                    string `json:"inst_country_name" db:"inst_country_name"`
		CongressionalDistrictCode  string `json:"cong_dist_code" db:"cong_dist_code"`
		StateCongressionalDistrict string `json:"st_cong_dist_code" db:"st_cong_dist_code"`
		LegalBusinessName          string `json:"org_lgl_bus_name" db:"org_lgl_bus_name"`
		ParentUEI                  string `json:"org_prnt_uei_num" db:"org_prnt_uei_num"`
		InstitutionUEI             string `json:"org_uei_num" db:"org_uei_num"`
	} `json:"inst" db:"inst"`
	PerformingInsitute struct {
		InstituteName              string `json:"perf_inst_name" db:"perf_inst_name"`
		StreetAddr                 string `json:"perf_str_addr" db:"perf_str_addr"`
		CityName                   string `json:"perf_city_name" db:"perf_city_name"`
		StateCode                  string `json:"perf_st_code" db:"perf_st_code"`
		StateName                  string `json:"perf_st_name" db:"perf_st_name"`
		ZipCode                    string `json:"perf_zip_code" db:"perf_zip_code"`
		CountryCode                string `json:"perf_ctry_code" db:"perf_ctry_code"`
		CongressionalDistrictCode  string `json:"perf_cong_dist" db:"perf_cong_dist"`
		StateCongressionalDistrict string `json:"perf_st_cong_dist" db:"perf_st_cong_dist"`
		CountryName                string `json:"perf_ctry_name" db:"perf_ctry_name"`
		CountryFlag                string `json:"perf_ctry_flag" db:"perf_ctry_flag"`
	} `json:"perf_inst" db:"perf_inst"`
	ProgramElements []struct {
		ProgramElementCode string `json:"pgm_ele_code" db:"pgm_ele_code"`
		ProgramElementName string `json:"pgm_ele_name" db:"pgm_ele_name"`
	} `json:"pgm_ele" db:"pgm_ele"`
	ProgramReference   string `json:"pgm_ref" db:"pgm_ref"`
	ApplicationFunding []struct {
		ApplicationCode     string `json:"app_code" db:"app_code"`
		ApplicationName     string `json:"app_name" db:"app_name"`
		ApplicationSymbolId string `json:"app_symb_id" db:"app_symb_id"`
		FundingCode         string `json:"fund_code" db:"fund_code"`
		FundingName         string `json:"fund_name" db:"fund_name"`
		FundingSymbolId     string `json:"fund_symb_id" db:"fund_symb_id"`
	} `json:"app_fund" db:"app_fund"`
	FundingObligations []struct {
		FiscalYear      int     `json:"fund_oblg_fiscal_yr" db:"fund_oblg_fiscal_yr"`
		AmountObligated float64 `json:"fund_oblg_amt" db:"fund_oblg_amt"`
	} `json:"oblg_fy" db:"oblg_fy"`
	ProjectOutcomesReport struct {
		HtmlContent string `json:"por_cntn" db:"por_cntn"`
		RawText     string `json:"por_txt_cntn" db:"por_txt_cntn"`
	} `json:"por" db:"por"`
}

type ResearchArea struct {
	AreaID         string   `json:"area_id" db:"area_id"`
	Name           string   `json:"name" db:"name"`
	Keywords       []string `json:"keywords" db:"keywords"`
	CSRankingsFlag bool     `json:"csrankings_flag" db:"csrankings_flag"`
	NSFFlag        bool     `json:"nsf_flag" db:"nsf_flag"`
}

type Investigator struct {
	Name          string `json:"name" db:"name"`
	Email         string `json:"email" db:"email"`
	InstitutionID string `json:"institution_id" db:"institution_id"`
	IsProfessor   bool   `json:"is_professor" db:"is_professor"`
}

type AwardAuthorLink struct {
	AwardID         string `json:"award_id" db:"award_id"`
	ContributorName string `json:"contributor_name" db:"contributor_name"`
	Role            string `json:"role" db:"role"`
}

type Country struct {
	Code      string `json:"code" db:"code"`
	Name      string `json:"name" db:"name"`
	Region    string `json:"region" db:"region"`
	Subregion string `json:"subregion" db:"subregion"`
}
