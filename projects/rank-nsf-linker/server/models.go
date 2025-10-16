package main

type NsfJsonData struct {
	AwdId                                  string  `json:"awd_id"`
	AgcyId                                 string  `json:"agcy_id"`
	TranType                               string  `json:"tran_type"`
	AwardInstrumentText                    string  `json:"awd_istr_txt"`
	AwardTitleText                         string  `json:"awd_titl_txt"`
	FederalCatalogDomesticAssistanceNumber string  `json:"cfda_num"`
	OrgCode                                string  `json:"org_code"`
	PoPhoneNumber                          string  `json:"po_phone"`
	PoEmailNumber                          string  `json:"po_email"`
	PoSignBlockName                        string  `json:"po_sign_block_name"`
	AwardEffectiveDate                     string  `json:"awd_eff_date"`
	AwardExpiryDate                        string  `json:"awd_exp_date"`
	TotalIntendedAwardAmount               float64 `json:"tot_intn_awd_amt"`
	AwardAmount                            float64 `json:"awd_amount"`
	EarliestAmendmentDate                  string  `json:"awd_min_amd_letter_date"`
	MostRecentAmendmentDate                string  `json:"awd_max_amd_letter_date"`
	AwardAbstract                          string  `json:"awd_abstract_narration"`
	AwardARRA                              float64 `json:"awd_arra_amount"`
	DirectorateAbbreviation                string  `json:"dir_abbr"`
	OrganizationDirectorateLongName        string  `json:"org_dir_long_name"`
	DivisionAbbreviation                   string  `json:"div_abbr"`
	OrganizationDivisionLongName           string  `json:"org_div_long_name"`
	AwardingAgencyCode                     string  `json:"awd_agcy_code"`
	FundingAgencyCode                      string  `json:"fund_agcy_code"`
	PrincipalInvestigators                 []struct {
		Role      string `json:"pi_role"`
		Name      string `json:"pi_full_name"`
		EmailAddr string `json:"pi_email_addr"`
		NSFId     string `json:"nsf_id"`
		StartDate string `json:"pi_start_date"`
		EndDate   string `json:"pi_end_date"`
	} `json:"pi"`
	Institute struct {
		Name                       string `json:"inst_name"`
		StreetAddress              string `json:"inst_street_address"`
		StreetAddressV2            string `json:"inst_street_address_2"`
		City                       string `json:"inst_city_name"`
		StateCode                  string `json:"inst_state_code"`
		StateName                  string `json:"inst_state_name"`
		PhoneNumber                string `json:"inst_phone_num"`
		ZipCode                    string `json:"inst_zip_code"`
		Country                    string `json:"inst_country_name"`
		CongressionalDistrictCode  string `json:"cong_dist_code"`
		StateCongressionalDistrict string `json:"st_cong_dist_code"`
		LegalBusinessName          string `json:"org_lgl_bus_name"`
		ParentUEI                  string `json:"org_prnt_uei_num"`
		InstitutionUEI             string `json:"org_uei_num"`
	} `json:"inst"`
	PerformingInsitute struct {
		InstituteName              string `json:"perf_inst_name"`
		StreetAddr                 string `json:"perf_str_addr"`
		CityName                   string `json:"perf_city_name"`
		StateCode                  string `json:"perf_st_code"`
		StateName                  string `json:"perf_st_name"`
		ZipCode                    string `json:"perf_zip_code"`
		CountryCode                string `json:"perf_ctry_code"`
		CongressionalDistrictCode  string `json:"perf_cong_dist"`
		StateCongressionalDistrict string `json:"perf_st_cong_dist"`
		CountryName                string `json:"perf_ctry_name"`
		CountryFlag                string `json:"perf_ctry_flag"`
	} `json:"perf_inst"`
	ProgramElements []struct {
		ProgramElementCode string `json:"pgm_ele_code"`
		ProgramElementName string `json:"pgm_ele_name"`
	} `json:"pgm_ele"`
	ProgramReference []struct {
		ProgramReferenceCode string `json:"pgm_ref_code"`
		ProgramReferenceName string `json:"pgm_ref_name"`
	} `json:"pgm_ref"`
	ApplicationFunding []struct {
		ApplicationCode     string `json:"app_code"`
		ApplicationName     string `json:"app_name"`
		ApplicationSymbolId string `json:"app_symb_id"`
		FundingCode         string `json:"fund_code"`
		FundingName         string `json:"fund_name"`
		FundingSymbolId     string `json:"fund_symb_id"`
	} `json:"app_fund"`
	FundingObligations []struct {
		FiscalYear      int     `json:"fund_oblg_fiscal_yr"`
		AmountObligated float64 `json:"fund_oblg_amt"`
	} `json:"oblg_fy"`
	ProjectOutcomesReport *struct {
		HtmlContent string `json:"por_cntn"`
		RawText     string `json:"por_txt_cntn"`
	} `json:"por"`
}
