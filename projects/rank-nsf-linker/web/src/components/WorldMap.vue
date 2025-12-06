<template>
  <div v-if="pipelineStatusMessage === ''" class="processing-overlay">
    <div class="processing-message">
      <span>Rendering map ...</span>
    </div>
  </div>

  <div
    v-if="pipelineStatusMessage === 'in-progress'"
    class="processing-overlay"
  >
    <div class="processing-message">
      <span>The server is currently being updated. Please wait ...</span>
    </div>
  </div>

  <div v-if="pipelineStatusMessage === 'failed'" class="processing-overlay">
    <div class="processing-message">
      <span
        >Server has run into an issue. Please reach out at
        saifulislam84210@gmail.com</span
      >
    </div>
  </div>

  <div v-if="pipelineStatusMessage === 'completed'" class="app" id="appMap">
    <div ref="mapContainer" id="map" class="map-container" />

    <!-- Enhanced Controls Panel -->
    <div class="controls-panel">
      <div class="search-section">
        <input
          v-model="search"
          @input="onSearchInput"
          @keydown.enter.prevent="searchAndFly"
          @focus="showSearchResults = true"
          placeholder="Search university, city, or state..."
          class="search"
        />
        <!-- Search Results Dropdown -->
        <div
          v-if="showSearchResults && searchResults.length > 0"
          class="search-results"
        >
          <div
            v-for="result in searchResults.slice(0, 5)"
            :key="result.institution"
            @click="flyToUniversity(result)"
            class="search-result-item"
          >
            <div class="result-name">{{ result.institution }}</div>
            <div class="result-location">
              {{ result.city }}, {{ result.region }}
            </div>
          </div>
        </div>
      </div>

      <!-- Semantic Research Search -->
      <div class="semantic-search-section">
        <div class="semantic-search-header">
          <span>🔬 Search by Research Topic</span>
        </div>
        <div class="semantic-search-input">
          <input
            v-model="researchQuery"
            @keydown.enter.prevent="searchByResearch"
            placeholder="e.g., 'machine learning for healthcare'"
            class="research-search-input"
          />
          <button
            @click="searchByResearch"
            class="search-btn"
            :disabled="!researchQuery.trim()"
          >
            Search
          </button>
        </div>

        <!-- Research Search Results -->
        <div v-if="researchSearching" class="research-loading">
          Searching...
        </div>
        <div v-else-if="researchResults.length > 0" class="research-results">
          <div class="results-header">
            Found {{ researchResults.length }} relevant faculty
          </div>
          <div
            v-for="(result, idx) in researchResults"
            :key="idx"
            @click="selectResearchResult(result)"
            class="research-result-item"
          >
            <div class="result-professor">
              {{ result.metadata.professor_name }}
              <span class="result-score"
                >{{ (result.score * 100).toFixed(0) }}% match</span
              >
            </div>
            <div class="result-title">{{ result.metadata.title }}</div>
            <div class="result-snippet">
              {{ result.metadata.content_snippet }}
            </div>
          </div>
        </div>
      </div>

      <!-- Filters -->
      <div class="filters-section">
        <button class="filter-toggle" @click="showFilters = !showFilters">
          {{ showFilters ? "▼" : "▶" }} Filters & Legend
        </button>

        <div v-if="showFilters" class="filters-content">
          <!-- Quick Presets -->
          <div class="filter-presets">
            <button @click="applyPreset('top-funded')" class="preset-btn">
              💰 Top Funded
            </button>
            <button @click="applyPreset('large-faculty')" class="preset-btn">
              👥 Large Faculty
            </button>
            <button @click="applyPreset('ai-focused')" class="preset-btn">
              🤖 AI Focused
            </button>
            <button @click="applyPreset('active-awards')" class="preset-btn">
              🏆 Active Awards
            </button>
          </div>

          <!-- Research Area Filter -->
          <div class="filter-group">
            <label>Research Areas:</label>
            <div class="area-chips">
              <button
                v-for="(color, area) in AREA_COLORS"
                :key="area"
                @click="toggleAreaFilter(area)"
                :class="['area-chip', { active: activeAreas.has(area) }]"
                :style="{
                  borderColor: color,
                  backgroundColor: activeAreas.has(area)
                    ? color
                    : 'transparent',
                  color: activeAreas.has(area) ? '#fff' : color,
                }"
              >
                {{ area }}
              </button>
            </div>
          </div>

          <!-- Funding Range Filter -->
          <div class="filter-group">
            <label>Funding Range (millions):</label>
            <div class="range-inputs">
              <input
                v-model.number="fundingMin"
                type="number"
                placeholder="Min"
                class="range-input"
              />
              <span>—</span>
              <input
                v-model.number="fundingMax"
                type="number"
                placeholder="Max"
                class="range-input"
              />
            </div>
          </div>

          <!-- Faculty Count Filter -->
          <div class="filter-group">
            <label>Faculty Count:</label>
            <div class="range-inputs">
              <input
                v-model.number="facultyMin"
                type="number"
                placeholder="Min"
                class="range-input"
              />
              <span>—</span>
              <input
                v-model.number="facultyMax"
                type="number"
                placeholder="Max"
                class="range-input"
              />
            </div>
          </div>

          <!-- Active Awards Filter -->
          <div class="filter-group">
            <label>
              <input v-model="showActiveAwardsOnly" type="checkbox" />
              Active NSF Awards Only
            </label>
          </div>

          <!-- State/Region Filter -->
          <div class="filter-group">
            <label>State/Region:</label>
            <select v-model="selectedState" class="viz-select">
              <option value="">All States</option>
              <option v-for="state in uniqueStates" :key="state" :value="state">
                {{ state }}
              </option>
            </select>
          </div>

          <!-- Sort Universities -->
          <div class="filter-group">
            <label>Sort Universities:</label>
            <select v-model="universitySort" class="viz-select">
              <option value="name">By Name</option>
              <option value="funding">By Funding (High to Low)</option>
              <option value="faculty">By Faculty Count (High to Low)</option>
              <option value="awards">By Active Awards (High to Low)</option>
            </select>
          </div>

          <!-- Visualization Mode -->
          <div class="filter-group">
            <label>Map Visualization:</label>
            <select v-model="vizMode" class="viz-select">
              <option value="area">By Research Area</option>
              <option value="funding">By Funding Amount</option>
              <option value="faculty">By Faculty Count</option>
              <option value="nsf">By NSF Awards</option>
            </select>
          </div>

          <button @click="resetFilters" class="reset-btn">Reset All</button>
        </div>
      </div>

      <!-- Stats Overview -->
      <div class="stats-overview">
        <div class="stat-item">
          <div class="stat-value">{{ sortedUniversities.length }}</div>
          <div class="stat-label">Universities</div>
        </div>
        <div class="stat-item">
          <div class="stat-value">{{ totalFaculty }}</div>
          <div class="stat-label">Faculty</div>
        </div>
        <div class="stat-item">
          <div class="stat-value">${{ totalFundingDisplay }}M</div>
          <div class="stat-label">Total Funding</div>
        </div>
        <div class="stat-item">
          <div class="stat-value">{{ totalActiveAwards }}</div>
          <div class="stat-label">Active Awards</div>
        </div>
      </div>
    </div>

    <!-- Enhanced Side Panel -->
    <aside class="side-panel" v-if="selectedUniversity">
      <button class="close" @click="closePanel">×</button>

      <div v-if="detailLoading" class="loading">Loading details...</div>

      <template v-else>
        <!-- University Header -->
        <div class="uni-header">
          <h2>{{ selectedUniversity.institution }}</h2>
          <div class="uni-meta">
            <span
              class="meta-badge"
              :style="{
                backgroundColor: getAreaColor(selectedUniversity.top_area),
              }"
            >
              {{ selectedUniversity.top_area }}
            </span>
          </div>
        </div>

        <!-- Quick Stats Grid -->
        <div class="quick-stats">
          <div class="stat-card">
            <div class="stat-icon">📍</div>
            <div class="stat-details">
              <div class="stat-label">Location</div>
              <div class="stat-value">
                {{ selectedUniversity.city }}, {{ selectedUniversity.country }}
              </div>
            </div>
          </div>

          <div class="stat-card">
            <div class="stat-icon">💰</div>
            <div class="stat-details">
              <div class="stat-label">Research Funding</div>
              <div class="stat-value">
                ${{ (selectedUniversity.funding || 0).toFixed(1) }}M
              </div>
            </div>
          </div>

          <div class="stat-card">
            <div class="stat-icon">🏆</div>
            <div class="stat-details">
              <div class="stat-label">NSF Awards</div>
              <div class="stat-value">
                <!-- {{ selectedUniversity.nsf_awards || 0 }} -->
              </div>
            </div>
          </div>

          <div class="stat-card">
            <div class="stat-icon">👥</div>
            <div class="stat-details">
              <div class="stat-label">Faculty</div>
              <div class="stat-value">
                {{ selectedUniversity.faculty_count || 0 }}
              </div>
            </div>
          </div>
        </div>

        <div class="uni-links">
          <a
            v-if="selectedUniversity.homepage"
            :href="selectedUniversity.homepage"
            target="_blank"
            class="link-btn"
          >
            🔗 Website
          </a>
        </div>

        <hr />

        <!-- Research Areas Distribution -->
        <div v-if="areaDistribution.length" class="section">
          <h3>Research Focus Distribution</h3>
          <div class="area-bars">
            <div
              v-for="area in areaDistribution"
              :key="area.name"
              class="area-bar-item"
            >
              <div class="area-bar-label">
                <span>{{ area.name }}</span>
                <span class="area-bar-count">{{ area.count }}</span>
              </div>
              <div class="area-bar-track">
                <div
                  class="area-bar-fill"
                  :style="{
                    width: area.percentage + '%',
                    backgroundColor: getAreaColor(area.name),
                  }"
                />
              </div>
            </div>
          </div>
        </div>

        <hr />

        <!-- Faculty Section with Sorting and Filtering -->
        <div class="section">
          <div class="section-header">
            <h3>Faculty ({{ filteredFaculty.length }})</h3>
            <div class="faculty-controls">
              <select v-model="facultySort" class="faculty-sort">
                <option value="name">Sort by Name</option>
                <option value="citations">Sort by Citations</option>
                <option value="publications">Sort by Publications</option>
                <option value="hindex">Sort by H-Index</option>
              </select>
            </div>
          </div>

          <!-- Area Filter for Faculty -->
          <div class="faculty-area-filter">
            <button
              v-for="area in uniqueFacultyAreas"
              :key="area"
              @click="toggleFacultyAreaFilter(area)"
              :class="[
                'area-filter-chip',
                { active: activeFacultyAreas.has(area) },
              ]"
              :style="{
                borderColor: getAreaColor(area),
                backgroundColor: activeFacultyAreas.has(area)
                  ? getAreaColor(area)
                  : 'transparent',
                color: activeFacultyAreas.has(area)
                  ? '#fff'
                  : getAreaColor(area),
              }"
            >
              {{ area }}
            </button>
          </div>

          <ul class="faculty-list">
            <li v-for="f in visibleFaculty" :key="f.name" class="fac-row">
              <div class="fac-content">
                <div class="fac-header">
                  <a
                    v-if="f.homepage"
                    :href="f.homepage"
                    target="_blank"
                    class="fac-name-link"
                  >
                    {{ f.name }}
                  </a>
                  <span v-else class="fac-name">{{ f.name }}</span>
                </div>

                <!-- <div v-if="f.dept" class="fac-dept">{{ f.dept }}</div> -->

                <div
                  v-if="f.matched_areas && f.matched_areas.length"
                  class="fac-areas"
                >
                  <span
                    v-for="area in f.matched_areas"
                    :key="area"
                    class="area-tag"
                    :style="{ backgroundColor: getAreaColor(area) }"
                  >
                    {{ area }}
                  </span>
                </div>

                <!-- Faculty Metrics -->
                <div
                  v-if="f.citations || f.publications || f.hindex"
                  class="fac-metrics"
                >
                  <span v-if="f.citations" class="metric"
                    >📊 {{ formatNumber(f.citations) }} citations</span
                  >
                  <span v-if="f.publications" class="metric"
                    >📄 {{ f.publications }} pubs</span
                  >
                  <span v-if="f.hindex" class="metric"
                    >📈 h-index: {{ f.hindex }}</span
                  >
                </div>

                <!-- Research Interests -->
                <div
                  v-if="f.interests && f.interests.length"
                  class="fac-interests"
                >
                  <em>{{ f.interests.join(", ") }}</em>
                </div>
              </div>
            </li>
          </ul>

          <button
            v-if="hasMoreFaculty"
            @click="showMoreFaculty"
            class="more-btn"
          >
            Show
            {{ Math.min(FAC_SLAB, filteredFaculty.length - visibleCount) }} more
          </button>
        </div>

        <!-- Recent NSF Awards Section -->
        <div
          v-if="
            selectedUniversity.recent_nsf_awards &&
            selectedUniversity.recent_nsf_awards.length
          "
          class="section"
        >
          <hr />
          <h3>
            Recent NSF Awards ({{
              selectedUniversity.recent_nsf_awards.length
            }})
          </h3>
          <ul class="nsf-awards-list">
            <li
              v-for="(award, idx) in selectedUniversity.recent_nsf_awards.slice(
                0,
                5
              )"
              :key="idx"
              class="nsf-award"
            >
              <div class="award-title">{{ award.title }}</div>
              <div class="award-meta">
                <span class="award-amount"
                  >${{ formatNumber(award.amount) }}</span
                >
                <!-- <span class="award-year">{{ award.year }}</span>
                <span v-if="award.program" class="award-program">{{
                  award.program
                }}</span> -->
              </div>
            </li>
          </ul>
        </div>
      </template>
    </aside>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, computed, watch } from "vue";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import axios from "axios";
import lodash from "lodash";
import pLimit from "p-limit";

const COUNTRIES_LIST = [
  "Afghanistan",
  "Åland Islands",
  "Albania",
  "Algeria",
  "American Samoa",
  "Andorra",
  "Angola",
  "Anguilla",
  "Antarctica",
  "Antigua and Barbuda",
  "Argentina",
  "Armenia",
  "Aruba",
  "Australia",
  "Austria",
  "Azerbaijan",
  "Bahamas",
  "Bahrain",
  "Bangladesh",
  "Barbados",
  "Belarus",
  "Belgium",
  "Belize",
  "Benin",
  "Bermuda",
  "Bhutan",
  "Bolivia",
  "Bonaire, Sint Eustatius and Saba",
  "Bosnia And Herzegovina",
  "Botswana",
  "Bouvet Island",
  "Brazil",
  "British Indian Ocean Territory",
  "Brunei Darussalam",
  "Bulgaria",
  "Burkina Faso",
  "Burundi",
  "Cabo Verde",
  "Cambodia",
  "Cameroon",
  "Canada",
  "Cayman Islands",
  "Central African Republic",
  "Chad",
  "Chile",
  "China",
  "Christmas Island",
  "Cocos (Keeling) Islands",
  "Colombia",
  "Comoros",
  "Congo",
  "Congo (Democratic Republic Of The)",
  "Cook Islands",
  "Costa Rica",
  "Côte D'Ivoire",
  "Croatia",
  "Cuba",
  "Curaçao",
  "Cyprus",
  "Czech Republic",
  "Denmark",
  "Djibouti",
  "Dominica",
  "Dominican Republic",
  "Ecuador",
  "Egypt",
  "El Salvador",
  "Equatorial Guinea",
  "Eritrea",
  "Estonia",
  "Eswatini",
  "Ethiopia",
  "Falkland Islands (Malvinas)",
  "Faroe Islands",
  "Fiji",
  "Finland",
  "France",
  "French Guiana",
  "French Polynesia",
  "French Southern Territories",
  "Gabon",
  "Gambia",
  "Georgia",
  "Germany",
  "Ghana",
  "Gibraltar",
  "Greece",
  "Greenland",
  "Grenada",
  "Guadeloupe",
  "Guam",
  "Guatemala",
  "Guernsey",
  "Guinea",
  "Guinea Bissau",
  "Guyana",
  "Haiti",
  "Heard Island and McDonald Islands",
  "Holy See",
  "Honduras",
  "Hong Kong",
  "Hungary",
  "Iceland",
  "India",
  "Indonesia",
  "Iran",
  "Iraq",
  "Ireland",
  "Isle of Man",
  "Israel",
  "Italy",
  "Jamaica",
  "Japan",
  "Jersey",
  "Jordan",
  "Kazakhstan",
  "Kenya",
  "Kiribati",
  "South Korea",
  "South Korea",
  "Kuwait",
  "Kyrgyzstan",
  "Laos",
  "Latvia",
  "Lebanon",
  "Lesotho",
  "Liberia",
  "Libya",
  "Liechtenstein",
  "Lithuania",
  "Luxembourg",
  "Macao",
  "Madagascar",
  "Malawi",
  "Malaysia",
  "Maldives",
  "Mali",
  "Malta",
  "Marshall Islands",
  "Martinique",
  "Mauritania",
  "Mauritius",
  "Mayotte",
  "Mexico",
  "Micronesia (Federated States of)",
  "Moldova",
  "Monaco",
  "Mongolia",
  "Montenegro",
  "Montserrat",
  "Morocco",
  "Mozambique",
  "Myanmar",
  "Namibia",
  "Nauru",
  "Nepal",
  "Netherlands",
  "New Caledonia",
  "New Zealand",
  "Nicaragua",
  "Niger",
  "Nigeria",
  "Niue",
  "Norfolk Island",
  "Macedonia",
  "Northern Mariana Islands",
  "Norway",
  "Oman",
  "Pakistan",
  "Palau",
  "Palestine",
  "Panama",
  "Papua New Guinea",
  "Paraguay",
  "Peru",
  "Philippines",
  "Pitcairn",
  "Poland",
  "Portugal",
  "Puerto Rico",
  "Qatar",
  "Réunion",
  "Romania",
  "Russia",
  "Rwanda",
  "Saint Barthélemy",
  "Saint Helena, Ascension and Tristan da Cunha",
  "Saint Kitts and Nevis",
  "Saint Lucia",
  "Saint Martin (French part)",
  "Saint Pierre and Miquelon",
  "Saint Vincent and the Grenadines",
  "Samoa",
  "San Marino",
  "Sao Tome and Principe",
  "Saudi Arabia",
  "Senegal",
  "Serbia",
  "Seychelles",
  "Sierra Leone",
  "Singapore",
  "Sint Maarten (Dutch part)",
  "Slovakia",
  "Slovenia",
  "Solomon Islands",
  "Somalia",
  "South Africa",
  "South Georgia and the South Sandwich Islands",
  "South Sudan",
  "Spain",
  "Sri Lanka",
  "Sudan",
  "Suriname",
  "Svalbard and Jan Mayen",
  "Sweden",
  "Switzerland",
  "Syria",
  "Taiwan",
  "Tajikistan",
  "Tanzania",
  "Thailand",
  "Timor-Leste",
  "Togo",
  "Tokelau",
  "Tonga",
  "Trinidad and Tobago",
  "Tunisia",
  "Turkey",
  "Turkmenistann",
  "Turks and Caicos Islands",
  "Tuvalu",
  "Uganda",
  "Ukraine",
  "United Arab Emirates",
  "United Kingdom",
  "United States",
  "United States Minor Outlying Islands",
  "Uruguay",
  "Uzbekistan",
  "Vanuatu",
  "Venezuela",
  "Vietnam",
  "Virgin Islands (British)",
  "Virgin Islands (U.S.)",
  "Wallis and Futuna",
  "Western Sahara",
  "Yemen",
  "Zambia",
  "Zimbabwe",
];

type AreaSubgroup = {
  name: string;
  subareas: string[];
};

type AreaGroup = Record<string, AreaSubgroup>;

type AreaGroups = Record<string, AreaGroup>;

// @ts-expect-error --- IGNORE ---
const AREA_GROUPS: AreaGroups = {
  AI: {
    AI: {
      name: "Artificial intelligence",
      subareas: ["aaai", "ijcai"],
    },
    ML: {
      name: "Machine learning",
      subareas: ["mlmining", "icml", "kdd", "iclr", "nips"],
    },
    NLP: {
      name: "Natural language processing",
      subareas: ["nlp", "acl", "emnlp", "naacl"],
    },
    Vision: {
      name: "Computer vision",
      subareas: ["vision", "cvpr", "eccv", "iccv"],
    },
    WebIR: {
      name: "The Web & information retrieval",
      subareas: ["inforet", "sigir", "www"],
    },
  },
  Systems: {
    Arch: {
      name: "Computer architecture",
      subareas: ["arch", "asplos", "isca", "micro", "hpca"],
    },
    Net: {
      name: "Computer networks",
      subareas: ["comm", "sigcomm", "nsdi"],
    },
    Sec: {
      name: "Computer security",
      subareas: ["sec", "ccs", "oakland", "usenixsec", "ndss", "pets"],
    },
    DB: {
      name: "Databases",
      subareas: ["mod", "sigmod", "vldb", "icde", "pods"],
    },
    EDA: {
      name: "Design automation",
      subareas: ["eda", "dac", "iccad"],
    },
    Emb: {
      name: "Embedded & real-time systems",
      subareas: ["bed", "emsoft", "rtas", "rtss"],
    },
    HPC: {
      name: "High-performance computing",
      subareas: ["hpc", "sc", "hpdc", "ics"],
    },
    Mobile: {
      name: "Mobile computing",
      subareas: ["mobile", "mobicom", "mobisys", "sensys"],
    },
    Metrics: {
      name: "Measurement & perf. analysis",
      subareas: ["metrics", "imc", "sigmetrics"],
    },
    OS: {
      name: "Operating systems",
      subareas: ["ops", "sosp", "osdi", "fast", "usenixatc", "eurosys"],
    },
    PL: {
      name: "Programming languages",
      subareas: ["pldi", "popl", "icfp", "oopsla", "plan"],
    },
    SE: {
      name: "Software engineering",
      subareas: ["soft", "fse", "icse", "ase", "issta"],
    },
  },
  Theory: {
    Theory: {
      name: "Algorithms & complexity",
      subareas: ["act", "focs", "soda", "stoc"],
    },
    Crypto: {
      name: "Cryptography",
      subareas: ["crypt", "crypto", "eurocrypt"],
    },
    Log: {
      name: "Logic & verification",
      subareas: ["log", "cav", "lics"],
    },
  },
  Interdisciplinary: {
    "Comp. Bio": {
      name: "Comp. bio & bioinformatics",
      subareas: ["bio", "ismb", "recomb"],
    },
    Graphics: {
      name: "Computer graphics",
      subareas: ["graph", "siggraph", "siggraph-asia", "eurographics"],
    },
    CSEd: {
      name: "Computer science education",
      subareas: ["csed", "sigcse"],
    },
    ECom: {
      name: "Economics & computation",
      subareas: ["ecom", "ec", "wine"],
    },
    HCI: {
      name: "Human-computer interaction",
      subareas: ["chi", "chiconf", "ubicomp", "uist"],
    },
    Robotics: {
      name: "Robotics",
      subareas: ["robotics", "icra", "iros", "rss"],
    },
    Visualization: {
      name: "Visualization",
      subareas: ["visualization", "vis", "vr"],
    },
  },
};

type ConferenceDict = Record<string, string>;

// @ts-expect-error --- IGNORE ---
const SUB_AREA_MAP: ConferenceDict = {
  aaai: "AAAI Conference on Artificial Intelligence",
  ijcai: "International Joint Conference on Artificial Intelligence",
  mlmining: "Data Mining and Knowledge Discovery",
  icml: "International Conference on Machine Learning",
  kdd: "ACM SIGKDD Conference on Knowledge Discovery and Data Mining",
  iclr: "International Conference on Learning Representations",
  nips: "Neural Information Processing Systems",
  nlp: "Natural Language Processing (General)",
  acl: "Annual Meeting of the Association for Computational Linguistics",
  emnlp: "Empirical Methods in Natural Language Processing",
  naacl:
    "North American Chapter of the Association for Computational Linguistics",
  vision: "Computer Vision (General)",
  cvpr: "IEEE Conference on Computer Vision and Pattern Recognition",
  eccv: "European Conference on Computer Vision",
  iccv: "International Conference on Computer Vision",
  inforet: "Information Retrieval (General)",
  sigir:
    "ACM SIGIR Conference on Research and Development in Information Retrieval",
  www: "International World Wide Web Conference",
  arch: "Computer Architecture (General)",
  asplos:
    "Architectural Support for Programming Languages and Operating Systems",
  isca: "International Symposium on Computer Architecture",
  micro: "IEEE/ACM International Symposium on Microarchitecture",
  hpca: "IEEE International Symposium on High-Performance Computer Architecture",
  comm: "Communications (General)",
  sigcomm: "ACM SIGCOMM Conference",
  nsdi: "USENIX Symposium on Networked Systems Design and Implementation",
  sec: "Computer Security (General)",
  ccs: "ACM Conference on Computer and Communications Security",
  oakland: "IEEE Symposium on Security and Privacy",
  usenixsec: "USENIX Security Symposium",
  ndss: "Network and Distributed System Security Symposium",
  pets: "Privacy Enhancing Technologies Symposium",
  mod: "Databases (General)",
  sigmod: "ACM SIGMOD International Conference on Management of Data",
  vldb: "International Conference on Very Large Data Bases",
  icde: "IEEE International Conference on Data Engineering",
  pods: "ACM Symposium on Principles of Database Systems",
  eda: "Electronic Design Automation (General)",
  dac: "Design Automation Conference",
  iccad: "International Conference on Computer-Aided Design",
  bed: "Embedded Systems (General)",
  emsoft: "International Conference on Embedded Software",
  rtas: "IEEE Real-Time and Embedded Technology and Applications Symposium",
  rtss: "IEEE Real-Time Systems Symposium",
  hpc: "High-Performance Computing (General)",
  sc: "International Conference for High Performance Computing, Networking, Storage and Analysis",
  hpdc: "ACM Symposium on High-Performance Parallel and Distributed Computing",
  ics: "ACM International Conference on Supercomputing",
  mobile: "Mobile Computing (General)",
  mobicom: "ACM International Conference on Mobile Computing and Networking",
  mobisys:
    "ACM International Conference on Mobile Systems, Applications, and Services",
  sensys: "ACM Conference on Embedded Networked Sensor Systems",
  metrics: "Performance Measurement (General)",
  imc: "ACM Internet Measurement Conference",
  sigmetrics: "ACM SIGMETRICS / IFIP Performance Conference",
  ops: "Operating Systems (General)",
  sosp: "ACM Symposium on Operating Systems Principles",
  osdi: "USENIX Symposium on Operating Systems Design and Implementation",
  fast: "USENIX Conference on File and Storage Technologies",
  usenixatc: "USENIX Annual Technical Conference",
  eurosys: "European Conference on Computer Systems",
  pldi: "Programming Language Design and Implementation",
  popl: "Principles of Programming Languages",
  icfp: "International Conference on Functional Programming",
  oopsla: "Object-Oriented Programming, Systems, Languages, and Applications",
  plan: "Programming Languages (General)",
  soft: "Software Engineering (General)",
  fse: "ACM SIGSOFT Symposium on the Foundations of Software Engineering",
  icse: "International Conference on Software Engineering",
  ase: "Automated Software Engineering Conference",
  issta: "International Symposium on Software Testing and Analysis",
  act: "Algorithms and Complexity Theory (General)",
  focs: "IEEE Symposium on Foundations of Computer Science",
  soda: "ACM-SIAM Symposium on Discrete Algorithms",
  stoc: "ACM Symposium on Theory of Computing",
  crypt: "Cryptography (General)",
  crypto: "International Cryptology Conference",
  eurocrypt: "European Symposium on Research in Computer Security",
  log: "Logic and Verification (General)",
  cav: "Computer Aided Verification",
  lics: "Logic in Computer Science",
  bio: "Computational Biology and Bioinformatics (General)",
  ismb: "Intelligent Systems for Molecular Biology",
  recomb: "Research in Computational Molecular Biology",
  graph: "Computer Graphics (General)",
  siggraph: "ACM SIGGRAPH Conference",
  "siggraph-asia": "ACM SIGGRAPH Asia",
  eurographics: "Eurographics Symposium",
  csed: "Computer Science Education (General)",
  sigcse: "ACM Technical Symposium on Computer Science Education",
  ecom: "Economics and Computation (General)",
  ec: "ACM Conference on Economics and Computation",
  wine: "Web and Internet Economics Conference",
  chi: "Human Factors in Computing Systems",
  chiconf: "ACM CHI Conference",
  ubicomp:
    "ACM International Joint Conference on Pervasive and Ubiquitous Computing",
  uist: "ACM Symposium on User Interface Software and Technology",
  robotics: "Robotics (General)",
  icra: "IEEE International Conference on Robotics and Automation",
  iros: "IEEE/RSJ International Conference on Intelligent Robots and Systems",
  rss: "Robotics: Science and Systems",
  visualization: "Visualization (General)",
  vis: "IEEE Visualization Conference",
  vr: "IEEE Conference on Virtual Reality and 3D User Interfaces",
};

// -------------------- Types --------------------
type Faculty = {
  name: string; // part of the schema
  homepage?: string; // part of the schema
  matched_areas?: string[];
  interests?: string[];
  citations?: number;
  publications?: number;
  hindex?: number;
};

type NSFAward = {
  title: string; // part of the schema, award_title_text
  amount: number; // part of the schema, award_amount
  years: number[]; // part of the schema, most_recent_amendment_date subtracted from earliest_amendment_date
};

type UniSummary = {
  institution: string; // part of schema
  longitude: number; // part of schema
  latitude: number; // part of schema
  top_area?: string; // for each university, get the faculty, get the distinct topic area for those faculty
  faculty_count?: number; // for each university, get the count of faculty
  funding?: number; // for each university, get the total funding, organize by year
};

type UniDetail = UniSummary & {
  city?: string; // part of schema
  country?: string; // part of schema
  homepage?: string; // part of schema
  faculty?: Faculty[]; // list of faculty with their details
  recent_nsf_awards?: NSFAward[]; // for each university, get recent NSF awards with details
};

// -------------------- Functions --------------------
function applyPreset(preset: string) {
  resetFilters();

  switch (preset) {
    case "top-funded":
      fundingMin.value = 100; // $100M+
      universitySort.value = "funding";
      break;
    case "large-faculty":
      facultyMin.value = 50;
      universitySort.value = "faculty";
      break;
    case "ai-focused":
      activeAreas.value = new Set(["AI"]);
      break;
    case "active-awards":
      showActiveAwardsOnly.value = true;
      universitySort.value = "awards";
      break;
  }
}

function onSearchInput() {
  if (!search.value.trim()) {
    searchResults.value = [];
    showSearchResults.value = false;
    return;
  }

  const query = search.value.toLowerCase().trim();
  searchResults.value = allUniversities.value.filter((u) => {
    const inst = u.institution.toLowerCase();
    const city = (u.city || "").toLowerCase();
    const region = (u.region || "").toLowerCase();

    // Match institution, city, or region
    return (
      inst.includes(query) || city.includes(query) || region.includes(query)
    );
  });

  showSearchResults.value = searchResults.value.length > 0;
}

function flyToUniversity(uni: UniSummary) {
  if (!map) return;

  showSearchResults.value = false;
  search.value = uni.institution;

  map.flyTo({
    center: [uni.longitude, uni.latitude],
    zoom: 12,
    duration: 1500,
  });

  // Select the university
  setTimeout(() => {
    selectUniversity(uni.institution);
  }, 1500);
}

async function searchByResearch() {
  if (!researchQuery.value.trim()) return;

  researchSearching.value = true;
  researchResults.value = [];

  try {
    const response = await axios.post("/api/search/faculty", {
      query: researchQuery.value,
      limit: 10,
    });

    researchResults.value = response.data;
    logger.Infof(
      `Found ${response.data.length} results for: ${researchQuery.value}`
    );
  } catch (err: any) {
    errorHandler(err, "Failed to search by research topic");
  } finally {
    researchSearching.value = false;
  }
}

function selectResearchResult(result: any) {
  const professorName = result.metadata.professor_name;

  // Find the professor's university
  const professor = allUniversities.value.find((u) =>
    u.faculty?.some((f) => f.name === professorName)
  );

  if (professor) {
    // Fly to university
    map?.flyTo({
      center: [professor.longitude, professor.latitude],
      zoom: 12,
      duration: 1500,
    });

    // Select university and highlight professor
    setTimeout(() => {
      selectUniversity(professor.institution);
    }, 1500);
  }
}

// -------------------- Config --------------------
const AREA_COLORS: Record<string, string> = {
  AI: "#10b981",
  Systems: "#3b82f6",
  Theory: "#8b5cf6",
  Interdisciplinary: "#f59e0b",
  Other: "#6b7280",
};

const FAC_SLAB = 25;
const CLUSTER_RADIUS = 60;
const POPUP_MAX_WIDTH = 300;

// -------------------- Refs & state --------------------
const mapContainer = ref<HTMLDivElement | null>(null);
let map: maplibregl.Map | null = null;

const allUniversities = ref<UniSummary[]>([]);
const universitiesById = new Map<string, UniSummary>();
const detailsCache = new Map<string, UniDetail>();

const selectedUniversity = ref<null | UniDetail>(null);
const selectedId = ref<string | null>(null);

const detailLoading = ref(false);
const pipelineStatusMessage = ref("");
const search = ref("");
const popupRef = ref<maplibregl.Popup | null>(null);

const visibleCount = ref(FAC_SLAB);

// Filter states
const showFilters = ref(false);
const activeAreas = ref(new Set<string>(Object.keys(AREA_COLORS)));
const fundingMin = ref<number | null>(null);
const fundingMax = ref<number | null>(null);
const facultyMin = ref<number | null>(null);
const facultyMax = ref<number | null>(null);
const showActiveAwardsOnly = ref(false);
const selectedState = ref<string>("");
const universitySort = ref<"name" | "funding" | "faculty" | "awards">("name");
const vizMode = ref<"area" | "funding" | "faculty" | "nsf">("area");

// Search
const showSearchResults = ref(false);
const searchResults = ref<UniSummary[]>([]);

// Research search
const researchQuery = ref("");
const researchSearching = ref(false);
const researchResults = ref<any[]>([]);

// Faculty filters
const facultySort = ref<"name" | "citations" | "publications" | "hindex">(
  "name"
);
const activeFacultyAreas = ref(new Set<string>());

// -------------------- Computed --------------------
const uniqueStates = computed(() => {
  const states = new Set<string>();
  allUniversities.value.forEach((u) => {
    if (u.region) states.add(u.region);
  });
  return Array.from(states).sort();
});

const filteredUniversities = computed(() => {
  return allUniversities.value.filter((u) => {
    // Area filter
    if (!activeAreas.value.has(u.top_area || "Other")) return false;

    // Funding filter
    if (fundingMin.value !== null && (u.funding || 0) < fundingMin.value)
      return false;
    if (fundingMax.value !== null && (u.funding || 0) > fundingMax.value)
      return false;

    // Faculty count filter
    if (facultyMin.value !== null && (u.faculty_count || 0) < facultyMin.value)
      return false;
    if (facultyMax.value !== null && (u.faculty_count || 0) > facultyMax.value)
      return false;

    // Active awards filter
    if (
      showActiveAwardsOnly.value &&
      (!u.stats?.active_awards || u.stats.active_awards === 0)
    )
      return false;

    // State filter
    if (selectedState.value && u.region !== selectedState.value) return false;

    return true;
  });
});

const sortedUniversities = computed(() => {
  const sorted = [...filteredUniversities.value];

  switch (universitySort.value) {
    case "funding":
      sorted.sort((a, b) => (b.funding || 0) - (a.funding || 0));
      break;
    case "faculty":
      sorted.sort((a, b) => (b.faculty_count || 0) - (a.faculty_count || 0));
      break;
    case "awards":
      sorted.sort(
        (a, b) => (b.stats?.active_awards || 0) - (a.stats?.active_awards || 0)
      );
      break;
    default:
      sorted.sort((a, b) => a.institution.localeCompare(b.institution));
  }

  return sorted;
});

const totalActiveAwards = computed(() =>
  filteredUniversities.value.reduce(
    (sum, u) => sum + (u.stats?.active_awards || 0),
    0
  )
);

const totalFaculty = computed(() =>
  filteredUniversities.value.reduce((sum, u) => sum + (u.faculty_count || 0), 0)
);

const totalFundingDisplay = computed(() =>
  filteredUniversities.value
    .reduce((sum, u) => sum + (u.funding || 0), 0)
    .toFixed(1)
);

const filteredFaculty = computed(() => {
  if (!selectedUniversity.value?.faculty) return [];

  let faculty = selectedUniversity.value.faculty;

  // Filter by area if any selected
  if (activeFacultyAreas.value.size > 0) {
    faculty = faculty.filter((f) =>
      f.matched_areas?.some((area) => activeFacultyAreas.value.has(area))
    );
  }

  // Sort
  const sorted = [...faculty];
  switch (facultySort.value) {
    case "citations":
      sorted.sort((a, b) => (b.citations || 0) - (a.citations || 0));
      break;
    case "publications":
      sorted.sort((a, b) => (b.publications || 0) - (a.publications || 0));
      break;
    case "hindex":
      sorted.sort((a, b) => (b.hindex || 0) - (a.hindex || 0));
      break;
    default:
      sorted.sort((a, b) => a.name.localeCompare(b.name));
  }

  return sorted;
});

const visibleFaculty = computed(() =>
  filteredFaculty.value.slice(0, visibleCount.value)
);

const hasMoreFaculty = computed(
  () => filteredFaculty.value.length > visibleCount.value
);

const areaDistribution = computed(() => {
  if (!selectedUniversity.value?.faculty) return [];

  const counts: Record<string, number> = {};
  selectedUniversity.value.faculty.forEach((f) => {
    f.matched_areas?.forEach((area) => {
      counts[area] = (counts[area] || 0) + 1;
    });
  });

  const total = Object.values(counts).reduce((sum, c) => sum + c, 0);

  return Object.entries(counts)
    .map(([name, count]) => ({
      name,
      count,
      percentage: total > 0 ? (count / total) * 100 : 0,
    }))
    .sort((a, b) => b.count - a.count);
});

const uniqueFacultyAreas = computed(() => {
  if (!selectedUniversity.value?.faculty) return [];
  const areas = new Set<string>();
  selectedUniversity.value.faculty.forEach((f) => {
    f.matched_areas?.forEach((area) => areas.add(area));
  });
  return Array.from(areas).sort();
});

// -------------------- Utilities --------------------
function shortLabel(name: string): string {
  if (!name) return "";
  const parts = name.split(/\s+/).slice(0, 3);
  return parts
    .map((p) => p[0])
    .join("")
    .toUpperCase()
    .slice(0, 4);
}

function formatNumber(num: number): string {
  if (num >= 1000000) return (num / 1000000).toFixed(1) + "M";
  if (num >= 1000) return (num / 1000).toFixed(1) + "K";
  return num.toString();
}

function getAreaColor(area?: string): string {
  return AREA_COLORS[area || "Other"] || AREA_COLORS.Other;
}

function buildFeatureCollection(summaries: UniSummary[]) {
  const features = summaries.map((u) => {
    universitiesById.set(u.institution, u);
    return {
      type: "Feature" as const,
      properties: {
        name: u.institution,
        top_area: u.top_area ?? "Other",
        label: shortLabel(u.institution),
        faculty_count: u.faculty_count ?? 0,
        funding: u.funding ?? 0,
        // nsf_awards: u.nsf_awards ?? 0,
      },
      geometry: {
        type: "Point" as const,
        coordinates: [u.longitude, u.latitude],
      },
    };
  });
  return { type: "FeatureCollection" as const, features };
}

function getMarkerColor(props: any, mode: string): string {
  switch (mode) {
    case "funding":
      const funding = props.funding || 0;
      if (funding > 100) return "#dc2626";
      if (funding > 50) return "#ea580c";
      if (funding > 20) return "#f59e0b";
      if (funding > 10) return "#84cc16";
      return "#6b7280";

    case "faculty":
      const count = props.faculty_count || 0;
      if (count > 100) return "#dc2626";
      if (count > 50) return "#ea580c";
      if (count > 25) return "#f59e0b";
      if (count > 10) return "#84cc16";
      return "#6b7280";

    case "nsf":
      const awards = props.nsf_awards || 0;
      if (awards > 50) return "#dc2626";
      if (awards > 25) return "#ea580c";
      if (awards > 10) return "#f59e0b";
      if (awards > 5) return "#84cc16";
      return "#6b7280";

    default: // area
      return getAreaColor(props.top_area);
  }
}

function getMarkerSize(props: any, mode: string): number {
  switch (mode) {
    case "funding":
      const funding = props.funding || 0;
      return Math.min(6 + Math.sqrt(funding) * 0.5, 20);

    case "faculty":
      const count = props.faculty_count || 0;
      return Math.min(6 + Math.sqrt(count) * 0.8, 20);

    case "nsf":
      const awards = props.nsf_awards || 0;
      return Math.min(6 + awards * 0.3, 20);

    default:
      return 10;
  }
}

// -------------------- Filter Functions --------------------
function toggleAreaFilter(area: string) {
  if (activeAreas.value.has(area)) {
    activeAreas.value.delete(area);
  } else {
    activeAreas.value.add(area);
  }
  activeAreas.value = new Set(activeAreas.value);
  updateMapData();
}

function toggleFacultyAreaFilter(area: string) {
  if (activeFacultyAreas.value.has(area)) {
    activeFacultyAreas.value.delete(area);
  } else {
    activeFacultyAreas.value.add(area);
  }
  activeFacultyAreas.value = new Set(activeFacultyAreas.value);
}

function resetFilters() {
  activeAreas.value = new Set(Object.keys(AREA_COLORS));
  fundingMin.value = null;
  fundingMax.value = null;
  facultyMin.value = null;
  facultyMax.value = null;
  showActiveAwardsOnly.value = false;
  selectedState.value = "";
  universitySort.value = "name";
  search.value = "";
  searchResults.value = [];
  showSearchResults.value = false;
  vizMode.value = "area";
  activeFacultyAreas.value = new Set();
  updateMapData();
}

function updatePointsLayer() {
  if (!map || !map.getSource("unis")) return;

  const fc = buildFeatureCollection(sortedUniversities.value);
  const source = map.getSource("unis") as maplibregl.GeoJSONSource;
  if (source) {
    source.setData(fc as any);
  }
}

async function fetchCountrySummaries(country: string): Promise<UniSummary[]> {
  const all: UniSummary[] = [];
  let page = 1;
  const pageSize = 50;
  let hasMore = true;

  while (hasMore) {
    const { data } = await axios.post<{
      results: UniSummary[];
      total: number;
      page: number;
      pageSize: number;
    }>("/api/universities/summary", {
      country,
      page,
      limit: pageSize,
    });

    all.push(...data.results);

    const totalPages = Math.ceil(data.total / pageSize);
    hasMore = page < totalPages;
    page++;
  }

  return all;
}

async function fetchAllSummaries(onCountryDone: (data: UniSummary[]) => void) {
  try {
    // Fetch top US universities from new endpoint
    const response = await axios.get<UniSummary[]>(
      "/api/universities/top?limit=100"
    );
    const data = response.data;
    onCountryDone(data);
    return data;
  } catch (err: any) {
    errorHandler(err, "Failed to fetch top universities");
    return [];
  }
}

async function setupMapWithSummaries(all: UniSummary[]) {
  const summaries = await fetchAllSummaries((data) => {
    if (!map) return;

    all.push(...data);

    const fc = buildFeatureCollection(all);

    map.addSource("unis", {
      type: "geojson",
      data: fc,
      cluster: true,
      clusterRadius: CLUSTER_RADIUS,
    });

    // Cluster layers
    map.addLayer({
      id: "clusters",
      type: "circle",
      source: "unis",
      filter: ["has", "point_count"],
      paint: {
        "circle-color": [
          "step",
          ["get", "point_count"],
          "#51bbd6",
          10,
          "#f1f075",
          30,
          "#f28cb1",
        ],
        "circle-radius": ["step", ["get", "point_count"], 18, 10, 26, 30, 36],
        "circle-opacity": 0.95,
      },
    });

    map.addLayer({
      id: "cluster-count",
      type: "symbol",
      source: "unis",
      filter: ["has", "point_count"],
      layout: { "text-field": "{point_count_abbreviated}", "text-size": 12 },
      paint: { "text-color": "#000" },
    });

    // Dynamic point colors based on viz mode
    updatePointsLayer();

    // Labels
    map.addLayer({
      id: "point-label",
      type: "symbol",
      source: "unis",
      filter: ["!", ["has", "point_count"]],
      layout: {
        "text-field": ["get", "label"],
        "text-size": 10,
        "text-font": ["Open Sans Semibold", "Arial Unicode MS Bold"],
      },
      paint: { "text-color": "#fff" },
    });

    // Selected highlight
    map.addLayer({
      id: "selected-point",
      type: "circle",
      source: "unis",
      filter: ["==", ["get", "id"], ""],
      paint: {
        "circle-color": "#ff6b6b",
        "circle-radius": 14,
        "circle-stroke-width": 3,
        "circle-stroke-color": "#fff",
      },
    });

    // Fit bounds
    const coords = fc.features.map((f: any) => f.geometry.coordinates);
    if (coords.length) {
      const lons = coords.map((c: any) => c[0]);
      const lats = coords.map((c: any) => c[1]);
      const minLon = Math.min(...lons),
        maxLon = Math.max(...lons),
        minLat = Math.min(...lats),
        maxLat = Math.max(...lats);
      map.fitBounds(
        [
          [minLon, minLat],
          [maxLon, maxLat],
        ],
        { padding: 40, maxZoom: 7, duration: 800 }
      );
    }

    // Click handlers
    map.on("click", "points", (e) => {
      const feature = e.features?.[0];
      if (!feature) return;
      const coords = (feature.geometry as any).coordinates.slice();
      const props = feature.properties as any;
      const id = props.id as string;
      const summary = universitiesById.get(id);
      if (!summary) return;

      popupRef.value?.remove();
      const html = `
          <div class="map-popup">
            <strong>${summary.institution}</strong><br/>
            <small>Faculty: ${props.faculty_count ?? 0}</small><br/>
            <small>Funding: $${(props.funding || 0).toFixed(1)}M</small><br/>
            <small>NSF Awards: ${props.nsf_awards || 0}</small><br/>
            <small style="color: #666;">Double-click for details</small>
          </div>`;

      if (map) {
        popupRef.value = new maplibregl.Popup({
          offset: 14,
          closeButton: true,
          className: "map-popup",
          maxWidth: `${POPUP_MAX_WIDTH}px`,
        })
          .setLngLat(coords as [number, number])
          .setHTML(html)
          .addTo(map);
      }
    });

    map.on("click", "clusters", async (e) => {
      const features = map!.queryRenderedFeatures(e.point, {
        layers: ["clusters"],
      });
      if (!features.length) return;
      const clusterId = features[0].properties.cluster_id;
      const source = map!.getSource("unis") as maplibregl.GeoJSONSource;
      const zoomVal = await source.getClusterExpansionZoom(clusterId);
      map!.easeTo({
        center:
          features[0].geometry.type === "Point"
            ? (features[0].geometry.coordinates as [number, number])
            : [0, 0],
        zoom: zoomVal,
        duration: 500,
      });
    });

    map.on("dblclick", "points", async (e) => {
      e.originalEvent?.preventDefault();
      const feature = e.features?.[0];
      if (!feature) return;
      const id = (feature.properties as any).id as string;

      if (detailsCache.has(id)) {
        selectedUniversity.value = detailsCache.get(id)!;
        visibleCount.value = FAC_SLAB;
        selectedId.value = id;
        activeFacultyAreas.value = new Set();
        updateSelectedFilter(id);
        return;
      }

      detailLoading.value = true;
      selectedUniversity.value = {
        id,
        institution: "Loading…",
        longitude: 0,
        latitude: 0,
        top_area: "Other",
        faculty_count: 0,
      } as UniDetail;

      try {
        const { data } = await axios.get<UniDetail>(`/api/universities/${id}`);
        detailsCache.set(id, data);
        selectedUniversity.value = data;
        visibleCount.value = FAC_SLAB;
        selectedId.value = id;
        activeFacultyAreas.value = new Set();
        updateSelectedFilter(id);
      } catch (err: any) {
        errorHandler(err, `Failed to fetch details for university ${id}`);
        selectedUniversity.value = null;
      } finally {
        detailLoading.value = false;
      }
    });

    ["points", "clusters"].forEach((layer) => {
      map!.on(
        "mouseenter",
        layer,
        () => (map!.getCanvas().style.cursor = "pointer")
      );
      map!.on("mouseleave", layer, () => (map!.getCanvas().style.cursor = ""));
    });
  });

  allUniversities.value = summaries;
  pipelineStatusMessage.value = "completed";
}

// -------------------- Core logic --------------------
onMounted(async () => {
  console.log("🗺️ Mounting component and initializing map...");

  if (!mapContainer.value) {
    // Initialise mapContainer if not present
    mapContainer.value = document.createElement("div");
    mapContainer.value.style.width = "100%";
    mapContainer.value.style.height = "100%";
  }

  console.log("🌍 Creating MapLibre instance...");
  map = new maplibregl.Map({
    container: mapContainer.value,
    style: {
      version: 8,
      sources: {
        osm: {
          type: "raster",
          tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],
          tileSize: 256,
        },
      },
      layers: [{ id: "osm", type: "raster", source: "osm" }],
    },
    center: [-95, 37], // Center of US
    zoom: 4, // Closer zoom for US
  });

  map.doubleClickZoom.disable();
  map.addControl(
    new maplibregl.NavigationControl({ showCompass: true }),
    "top-left"
  );
  map.addControl(new maplibregl.FullscreenControl(), "top-left");

  console.log(
    "✅ Map initialized successfully. Waiting for backend to be ready..."
  );

  const all: UniSummary[] = [];
  let attempt = 0;

  while (
    pipelineStatusMessage.value === "in-progress" ||
    !pipelineStatusMessage.value ||
    pipelineStatusMessage.value === ""
  ) {
    attempt++;
    console.log(`🔁 [Attempt ${attempt}] Checking backend health...`);

    try {
      await axios.get("/api/health");
      pipelineStatusMessage.value = "completed";
      console.log("✅ Backend is ready! Proceeding with data setup.");
    } catch (err: any) {
      if (axios.isAxiosError(err) && err.response) {
        let serverStatus = err.response.headers["server-status"] || "";
        const parts = serverStatus.split("/");
        const currentStatus = parts[1] || serverStatus;
        const retryAfter = parseInt(err.response.headers["Retry-After"], 10);

        pipelineStatusMessage.value = currentStatus;

        if (currentStatus === "in-progress") {
          console.warn(
            `⏳ Backend pipeline still in progress (retry after ${retryAfter}s)...`
          );
          await new Promise((resolve) =>
            setTimeout(resolve, retryAfter * 1000)
          );
        } else if (currentStatus === "failed") {
          console.error(
            "❌ Backend pipeline reported a permanent failure. Stopping retries."
          );
          errorHandler(
            new Error("Backend pipeline failed"),
            "Error fetching university summaries"
          );
          break;
        } else {
          console.warn(
            `⚠️ Received unknown backend status: "${currentStatus}". Retrying in ${retryAfter}s.`
          );
          await new Promise((resolve) =>
            setTimeout(resolve, retryAfter * 1000)
          );
        }
      } else {
        console.error("❗ Unexpected error while checking backend:", err);
        await new Promise((resolve) => setTimeout(resolve, 3000));
      }
    }
  }

  console.log("🚀 Starting map data setup...");
  try {
    await setupMapWithSummaries(all);
    console.log("🎉 Map data successfully loaded and rendered.");
  } catch (err: Error | any) {
    if (axios.isAxiosError(err) && err.response) {
      const httpStatus = err.response.status;
      console.error(`❌ Axios error during setup: HTTP ${httpStatus}`);
      if (httpStatus === 500) {
        pipelineStatusMessage.value = "failed";
        errorHandler(
          new Error("Backend service is unavailable (500)"),
          "Error fetching university summaries"
        );
      } else if (httpStatus === 503) {
        pipelineStatusMessage.value = "in-progress";
        console.warn("⚠️ Backend still in progress (503).");
      }
    } else {
      console.error("❗ Unexpected error during map setup:", err);
      errorHandler(err, "Error fetching university summaries");
    }
  }

  const mainMapContainer = document.getElementById("app");
  if (!mainMapContainer) {
    console.error("❌ Map container element with ID 'map' not found.");
    return;
  } else {
    mainMapContainer.appendChild(mapContainer.value);
  }
  console.log("🏁 onMounted completed execution.");
});

function errorHandler(err: Error, prefix = "") {
  const message = prefix ? `${prefix}: ${err.message}` : err.message;
  // Make a request to the logging-service
  axios
    .post("/ls/logs/log", {
      level: "error",
      message: message,
      stack: err.stack,
      timestamp: new Date().toISOString(),
    })
    .catch((loggingError) => {
      console.error(
        "Failed to log error to the logging service:",
        loggingError
      );
    });
}

function updatePointsLayer() {
  if (!map || !map.getLayer("points")) return;

  map.removeLayer("points");

  let circleColor: any;
  let circleRadius: any;

  // Use helper functions to build the MapLibre expressions
  switch (vizMode.value) {
    case "area":
      circleColor = ["match", ["get", "top_area"]];
      Object.entries(AREA_COLORS).forEach(([k, v]) => {
        circleColor.push(k, v);
      });
      circleColor.push(getMarkerColor({ top_area: "Other" }, "area")); // Default
      circleRadius = getMarkerSize({}, "area");
      break;

    case "funding":
      circleColor = [
        "step",
        ["get", "funding"],
        getMarkerColor({ funding: 0 }, "funding"), // Default
        10,
        getMarkerColor({ funding: 11 }, "funding"),
        20,
        getMarkerColor({ funding: 21 }, "funding"),
        50,
        getMarkerColor({ funding: 51 }, "funding"),
        100,
        getMarkerColor({ funding: 101 }, "funding"),
      ];
      circleRadius = [
        "interpolate",
        ["linear"],
        ["get", "funding"],
        0,
        getMarkerSize({ funding: 0 }, "funding"),
        200,
        getMarkerSize({ funding: 200 }, "funding"),
      ];
      break;

    case "faculty":
      circleColor = [
        "step",
        ["get", "faculty_count"],
        getMarkerColor({ faculty_count: 0 }, "faculty"), // Default
        10,
        getMarkerColor({ faculty_count: 11 }, "faculty"),
        25,
        getMarkerColor({ faculty_count: 26 }, "faculty"),
        50,
        getMarkerColor({ faculty_count: 51 }, "faculty"),
        100,
        getMarkerColor({ faculty_count: 101 }, "faculty"),
      ];
      circleRadius = getMarkerSize({}, "faculty"); // Simplified for now
      break;

    case "nsf":
      circleColor = ["step", ["get", "nsf_awards"]]; // Simplified for now
      circleRadius = getMarkerSize({}, "nsf"); // Simplified for now
      break;
  }

  map.addLayer(
    {
      id: "points",
      type: "circle",
      source: "unis",
      filter: ["!", ["has", "point_count"]],
      paint: {
        "circle-color": circleColor,
        "circle-radius": circleRadius,
        "circle-stroke-width": 1,
        "circle-stroke-color": "#fff",
        "circle-opacity": 0.9,
      },
    },
    "point-label"
  );
}

function updateSelectedFilter(id: string | null) {
  if (!map) return;
  const filter = ["==", ["get", "id"], id ?? ""];
  try {
    map.setFilter("selected-point", filter as any);
  } catch (e) {
    // layer may not be added yet
  }
}

// Search handlers
const onSearchInput = lodash.debounce(() => {}, 300);

function searchAndFly() {
  if (!map) return;
  const q = search.value.trim().toLowerCase();
  if (!q) return;
  for (const [id, u] of universitiesById) {
    if (u.institution.toLowerCase().includes(q)) {
      map.easeTo({ center: [u.longitude, u.latitude], zoom: 8, duration: 700 });
      if (!detailsCache.has(id))
        axios
          .get(`/api/universities/${id}`)
          .then((r) => detailsCache.set(id, r.data))
          .catch(() => {});
      return;
    }
  }
  console.warn("No match for", q);
}

function showMoreFaculty() {
  visibleCount.value += FAC_SLAB;
}

function closePanel() {
  selectedUniversity.value = null;
  selectedId.value = null;
  activeFacultyAreas.value = new Set();
  updateSelectedFilter(null);
}

// Watch for viz mode changes
watch(vizMode, () => {
  updatePointsLayer();
});

watch(selectedId, (id) => updateSelectedFilter(id ?? null));

onBeforeUnmount(() => {
  popupRef.value?.remove();
  map?.remove();
});
</script>

<style scoped>
* {
  box-sizing: border-box;
}

.app {
  height: 100vh;
  width: 100vw;
  position: relative;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Inter, Arial,
    sans-serif;
  background: #f8fafc;
}

.map-container {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  right: 420px;
}

/* Enhanced Controls Panel */
.controls-panel {
  position: absolute;
  left: 12px;
  top: 12px;
  z-index: 11;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1),
    0 2px 4px -1px rgba(0, 0, 0, 0.06);
  padding: 16px;
  max-width: 340px;
}

.search-section {
  margin-bottom: 12px;
  position: relative;
}

.search {
  width: 100%;
  padding: 10px 14px;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  font-size: 14px;
  transition: all 0.2s;
}

.search:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.search-results {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  margin-top: 4px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  z-index: 1000;
  max-height: 300px;
  overflow-y: auto;
}

.search-result-item {
  padding: 12px;
  cursor: pointer;
  border-bottom: 1px solid #f1f5f9;
  transition: background 0.2s;
}

.search-result-item:last-child {
  border-bottom: none;
}

.search-result-item:hover {
  background: #f8fafc;
}

.result-name {
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 4px;
}

.result-location {
  font-size: 12px;
  color: #64748b;
}

/* Semantic Research Search */
.semantic-search-section {
  margin-bottom: 16px;
  padding: 12px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 8px;
  color: white;
}

.semantic-search-header {
  font-weight: 600;
  font-size: 14px;
  margin-bottom: 8px;
}

.semantic-search-input {
  display: flex;
  gap: 8px;
}

.research-search-input {
  flex: 1;
  padding: 8px 12px;
  border-radius: 6px;
  border: none;
  font-size: 13px;
}

.research-search-input:focus {
  outline: none;
  box-shadow: 0 0 0 3px rgba(255, 255, 255, 0.3);
}

.search-btn {
  padding: 8px 16px;
  background: white;
  color: #667eea;
  border: none;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.search-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
}

.search-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.research-loading {
  margin-top: 12px;
  padding: 12px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 6px;
  text-align: center;
  font-size: 13px;
}

.research-results {
  margin-top: 12px;
  max-height: 400px;
  overflow-y: auto;
}

.results-header {
  font-size: 12px;
  font-weight: 600;
  margin-bottom: 8px;
  opacity: 0.9;
}

.research-result-item {
  padding: 12px;
  background: rgba(255, 255, 255, 0.95);
  color: #1e293b;
  border-radius: 6px;
  margin-bottom: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.research-result-item:hover {
  background: white;
  transform: translateX(4px);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.result-professor {
  font-weight: 600;
  font-size: 14px;
  margin-bottom: 4px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.result-score {
  font-size: 11px;
  background: #10b981;
  color: white;
  padding: 2px 8px;
  border-radius: 12px;
  font-weight: 600;
}

.result-title {
  font-size: 12px;
  color: #475569;
  margin-bottom: 4px;
}

.result-snippet {
  font-size: 11px;
  color: #64748b;
  line-height: 1.4;
}

.filters-section {
  border-top: 1px solid #e2e8f0;
  padding-top: 12px;
}

.filter-toggle {
  width: 100%;
  padding: 8px 12px;
  background: #f1f5f9;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
  font-size: 13px;
  text-align: left;
  transition: background 0.2s;
}

.filter-toggle:hover {
  background: #e2e8f0;
}

.filters-content {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #e2e8f0;
}

.filter-presets {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.preset-btn {
  flex: 1;
  min-width: 100px;
  padding: 8px 12px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.preset-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
}

.preset-btn:active {
  transform: translateY(0);
}

.filter-group {
  margin-bottom: 16px;
}

.filter-group label {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: #475569;
  margin-bottom: 8px;
}

.area-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.area-chip {
  padding: 6px 12px;
  border-radius: 20px;
  border: 2px solid;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.area-chip:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.range-inputs {
  display: flex;
  align-items: center;
  gap: 8px;
}

.range-input {
  flex: 1;
  padding: 6px 10px;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  font-size: 13px;
}

.viz-select {
  width: 100%;
  padding: 8px 10px;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  font-size: 13px;
  background: #fff;
  cursor: pointer;
}

.reset-btn {
  width: 100%;
  padding: 8px;
  background: #ef4444;
  color: #fff;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

.reset-btn:hover {
  background: #dc2626;
}

.stats-overview {
  display: flex;
  gap: 8px;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #e2e8f0;
}

.stat-item {
  flex: 1;
  text-align: center;
}

.stat-value {
  font-size: 18px;
  font-weight: 700;
  color: #1e293b;
}

.stat-label {
  font-size: 11px;
  color: #64748b;
  margin-top: 2px;
}

/* Enhanced Side Panel */
.side-panel {
  position: absolute;
  right: 0;
  top: 0;
  width: 420px;
  height: 100%;
  background: #fff;
  border-left: 1px solid #e2e8f0;
  padding: 24px;
  overflow: auto;
  z-index: 12;
  box-shadow: -4px 0 6px -1px rgba(0, 0, 0, 0.1);
}

.side-panel::-webkit-scrollbar {
  width: 8px;
}

.side-panel::-webkit-scrollbar-track {
  background: #f1f5f9;
}

.side-panel::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 4px;
}

.close {
  float: right;
  font-size: 24px;
  border: none;
  background: transparent;
  cursor: pointer;
  color: #64748b;
  line-height: 1;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  transition: all 0.2s;
}

.close:hover {
  background: #f1f5f9;
  color: #1e293b;
}

.loading {
  font-style: italic;
  color: #64748b;
  text-align: center;
  padding: 40px 0;
}

.uni-header {
  margin-bottom: 20px;
}

.uni-header h2 {
  margin: 0 0 8px 0;
  font-size: 22px;
  color: #1e293b;
  line-height: 1.3;
}

.uni-meta {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.meta-badge {
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
  color: #fff;
}

.meta-badge.ranking {
  background: #6366f1;
}

.quick-stats {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  margin-bottom: 20px;
}

.stat-card {
  display: flex;
  gap: 12px;
  padding: 12px;
  background: #f8fafc;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}

.stat-icon {
  font-size: 24px;
  flex-shrink: 0;
}

.stat-details {
  flex: 1;
  min-width: 0;
}

.stat-card .stat-label {
  font-size: 11px;
  color: #64748b;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 4px;
}

.stat-card .stat-value {
  font-size: 16px;
  font-weight: 700;
  color: #1e293b;
  overflow: hidden;
  text-overflow: ellipsis;
}

.uni-links {
  margin-bottom: 20px;
}

.link-btn {
  display: inline-block;
  padding: 8px 16px;
  background: #3b82f6;
  color: #fff;
  text-decoration: none;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 600;
  transition: background 0.2s;
}

.link-btn:hover {
  background: #2563eb;
}

hr {
  border: none;
  border-top: 1px solid #e2e8f0;
  margin: 20px 0;
}

.section {
  margin-bottom: 24px;
}

.section h3 {
  margin: 0 0 12px 0;
  font-size: 16px;
  color: #1e293b;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.section-header h3 {
  margin: 0;
}

/* Research Area Distribution */
.area-bars {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.area-bar-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.area-bar-label {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  font-weight: 600;
  color: #475569;
}

.area-bar-count {
  color: #94a3b8;
}

.area-bar-track {
  height: 8px;
  background: #e2e8f0;
  border-radius: 4px;
  overflow: hidden;
}

.area-bar-fill {
  height: 100%;
  transition: width 0.3s ease;
  border-radius: 4px;
}

/* Faculty Section */
.faculty-controls {
  display: flex;
  gap: 8px;
}

.faculty-sort {
  padding: 6px 10px;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  font-size: 12px;
  background: #fff;
  cursor: pointer;
}

.faculty-area-filter {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 12px;
}

.area-filter-chip {
  padding: 4px 10px;
  border-radius: 16px;
  border: 1.5px solid;
  font-size: 11px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.area-filter-chip:hover {
  transform: translateY(-1px);
}

.faculty-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.fac-row {
  padding: 14px 0;
  border-bottom: 1px solid #f1f5f9;
}

.fac-row:last-child {
  border-bottom: none;
}

.fac-content {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.fac-header {
  display: flex;
  align-items: baseline;
}

.fac-name-link {
  color: #2563eb;
  text-decoration: none;
  font-weight: 600;
  font-size: 14px;
}

.fac-name-link:hover {
  text-decoration: underline;
}

.fac-name {
  font-weight: 600;
  font-size: 14px;
  color: #1e293b;
}

.fac-dept {
  font-size: 12px;
  color: #64748b;
}

.fac-areas {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.area-tag {
  padding: 3px 8px;
  border-radius: 10px;
  font-size: 10px;
  font-weight: 600;
  color: #fff;
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

.fac-metrics {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  font-size: 11px;
  color: #64748b;
}

.metric {
  display: flex;
  align-items: center;
  gap: 4px;
}

.fac-interests {
  font-size: 12px;
  color: #64748b;
  line-height: 1.4;
}

.more-btn {
  width: 100%;
  margin-top: 12px;
  padding: 10px;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  background: #fff;
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
  color: #3b82f6;
  transition: all 0.2s;
}

.more-btn:hover {
  background: #f8fafc;
  border-color: #3b82f6;
}

/* NSF Awards */
.nsf-awards-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.nsf-award {
  padding: 12px;
  background: #f8fafc;
  border-radius: 8px;
  margin-bottom: 8px;
  border-left: 3px solid #3b82f6;
}

.award-title {
  font-size: 13px;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 6px;
  line-height: 1.4;
}

.award-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  font-size: 11px;
  color: #64748b;
}

.award-amount {
  font-weight: 700;
  color: #059669;
}

.award-year {
  color: #6366f1;
  font-weight: 600;
}

.award-program {
  background: #e0e7ff;
  color: #4338ca;
  padding: 2px 8px;
  border-radius: 10px;
  font-weight: 600;
}

/* Map Popup */
.map-popup {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif;
  line-height: 1.5;
  padding: 4px;
}

.map-popup strong {
  color: #1e293b;
  font-size: 14px;
}

.map-popup small {
  font-size: 12px;
  color: #64748b;
  display: block;
  margin-top: 2px;
}

.processing-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.85);
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
}
.processing-message {
  font-size: 2rem;
  color: #333;
  font-weight: bold;
  background: #fff;
  padding: 2rem 3rem;
  border-radius: 16px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.08);
}

/* Responsive adjustments */
@media (max-width: 1024px) {
  .map-container {
    right: 360px;
  }

  .side-panel {
    width: 360px;
  }

  .controls-panel {
    max-width: 280px;
  }
}

@media (max-width: 768px) {
  .map-container {
    right: 0;
    bottom: 50%;
  }

  .side-panel {
    width: 100%;
    height: 50%;
    top: auto;
    bottom: 0;
    border-left: none;
    border-top: 1px solid #e2e8f0;
  }

  .controls-panel {
    max-width: calc(100vw - 24px);
  }

  .quick-stats {
    grid-template-columns: repeat(3, 1fr);
  }
}
</style>
