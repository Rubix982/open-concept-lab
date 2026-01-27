const STORAGE_KEY = "preferred_country";
const DEFAULT_COUNTRY = "USA";

export function getStoredCountry(): string {
  try {
    return localStorage.getItem(STORAGE_KEY) || DEFAULT_COUNTRY;
  } catch (error) {
    console.warn("Failed to load country preference", error);
    return DEFAULT_COUNTRY;
  }
}

export function setStoredCountry(country: string): void {
  try {
    localStorage.setItem(STORAGE_KEY, country);
  } catch (error) {
    console.warn("Failed to save country preference", error);
  }
}
