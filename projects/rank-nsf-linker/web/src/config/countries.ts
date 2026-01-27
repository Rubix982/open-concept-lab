// src/config/countries.ts

export interface Boundary {
  top: number;
  bottom: number;
  left: number;
  right: number;
}

// Helper to convert to Mapbox bounds format
export type MapboxBounds = [[number, number], [number, number]]; // [[west, south], [east, north]]

export interface BoundedCountry {
  name: string;
  code: string;
  longitude: number;
  latitude: number;
  bounds: Boundary;
  zoom: number;
}

// Utility function
export function toMapboxBounds(boundary: Boundary): MapboxBounds {
  return [
    [boundary.left, boundary.bottom], // Southwest
    [boundary.right, boundary.top], // Northeast
  ];
}

export const COUNTRIES: BoundedCountry[] = [
  // North America
  {
    name: "United States Of America",
    code: "USA",
    longitude: -95.7129,
    latitude: 37.0902,
    bounds: {
      top: 49.384,
      bottom: 24.396,
      left: -124.848,
      right: -66.865,
    },
    zoom: 4,
  },
  {
    name: "Canada",
    code: "CAN",
    longitude: -106.3468,
    latitude: 56.1304,
    bounds: {
      top: 83.11,
      bottom: 41.676,
      left: -141.0,
      right: -52.636,
    },
    zoom: 3,
  },
  {
    name: "Mexico",
    code: "MEX",
    longitude: -102.5528,
    latitude: 23.6345,
    bounds: {
      top: 32.719,
      bottom: 14.532,
      left: -118.404,
      right: -86.703,
    },
    zoom: 5,
  },

  // Europe
  {
    name: "United Kingdom",
    code: "GBR",
    longitude: -3.436,
    latitude: 55.3781,
    bounds: {
      top: 60.861,
      bottom: 49.674,
      left: -8.649,
      right: 1.763,
    },
    zoom: 5,
  },
  {
    name: "Germany",
    code: "DEU",
    longitude: 10.4515,
    latitude: 51.1657,
    bounds: {
      top: 55.058,
      bottom: 47.27,
      left: 5.866,
      right: 15.042,
    },
    zoom: 6,
  },
  {
    name: "France",
    code: "FRA",
    longitude: 2.2137,
    latitude: 46.2276,
    bounds: {
      top: 51.089,
      bottom: 41.333,
      left: -5.143,
      right: 9.56,
    },
    zoom: 6,
  },
  {
    name: "Italy",
    code: "ITA",
    longitude: 12.5674,
    latitude: 41.8719,
    bounds: {
      top: 47.092,
      bottom: 36.619,
      left: 6.627,
      right: 18.52,
    },
    zoom: 6,
  },
  {
    name: "Spain",
    code: "ESP",
    longitude: -3.7492,
    latitude: 40.4637,
    bounds: {
      top: 43.791,
      bottom: 36.0,
      left: -9.301,
      right: 3.323,
    },
    zoom: 6,
  },
  {
    name: "Netherlands",
    code: "NLD",
    longitude: 5.2913,
    latitude: 52.1326,
    bounds: {
      top: 53.555,
      bottom: 50.75,
      left: 3.358,
      right: 7.227,
    },
    zoom: 7,
  },
  {
    name: "Switzerland",
    code: "CHE",
    longitude: 8.2275,
    latitude: 46.8182,
    bounds: {
      top: 47.808,
      bottom: 45.818,
      left: 5.956,
      right: 10.492,
    },
    zoom: 7,
  },
  {
    name: "Sweden",
    code: "SWE",
    longitude: 18.6435,
    latitude: 60.1282,
    bounds: {
      top: 69.06,
      bottom: 55.336,
      left: 11.027,
      right: 24.167,
    },
    zoom: 5,
  },
  {
    name: "Norway",
    code: "NOR",
    longitude: 8.4689,
    latitude: 60.472,
    bounds: {
      top: 71.185,
      bottom: 57.977,
      left: 4.65,
      right: 31.078,
    },
    zoom: 5,
  },
  {
    name: "Denmark",
    code: "DNK",
    longitude: 9.5018,
    latitude: 56.2639,
    bounds: {
      top: 57.751,
      bottom: 54.559,
      left: 8.076,
      right: 15.158,
    },
    zoom: 7,
  },
  {
    name: "Poland",
    code: "POL",
    longitude: 19.1451,
    latitude: 51.9194,
    bounds: {
      top: 54.836,
      bottom: 49.002,
      left: 14.123,
      right: 24.146,
    },
    zoom: 6,
  },

  // Asia
  {
    name: "China",
    code: "CHN",
    longitude: 104.1954,
    latitude: 35.8617,
    bounds: {
      top: 53.561,
      bottom: 18.197,
      left: 73.557,
      right: 135.026,
    },
    zoom: 4,
  },
  {
    name: "Japan",
    code: "JPN",
    longitude: 138.2529,
    latitude: 36.2048,
    bounds: {
      top: 45.523,
      bottom: 30.983,
      left: 129.408,
      right: 145.543,
    },
    zoom: 5,
  },
  {
    name: "India",
    code: "IND",
    longitude: 78.9629,
    latitude: 20.5937,
    bounds: {
      top: 35.504,
      bottom: 6.746,
      left: 68.177,
      right: 97.395,
    },
    zoom: 5,
  },
  {
    name: "South Korea",
    code: "KOR",
    longitude: 127.7669,
    latitude: 35.9078,
    bounds: {
      top: 38.612,
      bottom: 33.113,
      left: 125.887,
      right: 129.584,
    },
    zoom: 7,
  },
  {
    name: "Singapore",
    code: "SGP",
    longitude: 103.8198,
    latitude: 1.3521,
    bounds: {
      top: 1.471,
      bottom: 1.258,
      left: 103.639,
      right: 104.007,
    },
    zoom: 11,
  },

  // Oceania
  {
    name: "Australia",
    code: "AUS",
    longitude: 133.7751,
    latitude: -25.2744,
    bounds: {
      top: -10.062,
      bottom: -43.644,
      left: 113.338,
      right: 153.569,
    },
    zoom: 4,
  },
  {
    name: "New Zealand",
    code: "NZL",
    longitude: 174.886,
    latitude: -40.9006,
    bounds: {
      top: -34.389,
      bottom: -47.286,
      left: 166.509,
      right: 178.517,
    },
    zoom: 6,
  },

  // South America
  {
    name: "Brazil",
    code: "BRA",
    longitude: -51.9253,
    latitude: -14.235,
    bounds: {
      top: 5.272,
      bottom: -33.751,
      left: -73.983,
      right: -34.793,
    },
    zoom: 4,
  },
  {
    name: "Argentina",
    code: "ARG",
    longitude: -63.6167,
    latitude: -38.4161,
    bounds: {
      top: -21.781,
      bottom: -55.061,
      left: -73.56,
      right: -53.638,
    },
    zoom: 4,
  },
  {
    name: "Chile",
    code: "CHL",
    longitude: -71.543,
    latitude: -35.6751,
    bounds: {
      top: -17.498,
      bottom: -55.926,
      left: -75.644,
      right: -66.417,
    },
    zoom: 4,
  },

  // Africa
  {
    name: "South Africa",
    code: "ZAF",
    longitude: 22.9375,
    latitude: -30.5595,
    bounds: {
      top: -22.126,
      bottom: -34.839,
      left: 16.458,
      right: 32.895,
    },
    zoom: 6,
  },
  {
    name: "Egypt",
    code: "EGY",
    longitude: 30.8025,
    latitude: 26.8206,
    bounds: {
      top: 31.668,
      bottom: 22.0,
      left: 24.698,
      right: 36.898,
    },
    zoom: 6,
  },
  {
    name: "Nigeria",
    code: "NGA",
    longitude: 8.6753,
    latitude: 9.082,
    bounds: {
      top: 13.892,
      bottom: 4.277,
      left: 2.692,
      right: 14.678,
    },
    zoom: 6,
  },

  // Middle East
  {
    name: "Saudi Arabia",
    code: "SAU",
    longitude: 45.0792,
    latitude: 23.8859,
    bounds: {
      top: 32.154,
      bottom: 16.379,
      left: 34.496,
      right: 55.667,
    },
    zoom: 5,
  },
  {
    name: "United Arab Emirates",
    code: "ARE",
    longitude: 53.8478,
    latitude: 23.4241,
    bounds: {
      top: 26.084,
      bottom: 22.633,
      left: 51.583,
      right: 56.382,
    },
    zoom: 8,
  },
];
