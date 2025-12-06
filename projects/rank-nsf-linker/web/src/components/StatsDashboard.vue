<template>
  <div class="stats-dashboard" :class="{ collapsed: isCollapsed }">
    <div class="dashboard-header">
      <h2>📊 Platform Statistics</h2>
      <button class="toggle-btn" @click="isCollapsed = !isCollapsed">
        {{ isCollapsed ? "▼ Show Stats" : "▲ Hide Stats" }}
      </button>
    </div>

    <div v-if="!isCollapsed" class="dashboard-content">
      <div class="stats-grid">
        <!-- University Count -->
        <div class="stat-card">
          <div class="stat-icon">🏛️</div>
          <div class="stat-content">
            <div class="stat-value">
              {{ stats.universityCount?.toLocaleString() || "..." }}
            </div>
            <div class="stat-label">Universities</div>
          </div>
        </div>

        <!-- Professor Count -->
        <div class="stat-card">
          <div class="stat-icon">👨‍🏫</div>
          <div class="stat-content">
            <div class="stat-value">
              {{ stats.professorCount?.toLocaleString() || "..." }}
            </div>
            <div class="stat-label">Professors</div>
          </div>
        </div>

        <!-- Award Count -->
        <div class="stat-card">
          <div class="stat-icon">🏆</div>
          <div class="stat-content">
            <div class="stat-value">
              {{ stats.awardCount?.toLocaleString() || "..." }}
            </div>
            <div class="stat-label">NSF Awards</div>
          </div>
        </div>

        <!-- Total Funding -->
        <div class="stat-card">
          <div class="stat-icon">💰</div>
          <div class="stat-content">
            <div class="stat-value">
              ${{ formatFunding(stats.totalFunding) }}
            </div>
            <div class="stat-label">Total Funding</div>
          </div>
        </div>

        <!-- Average Funding -->
        <div class="stat-card">
          <div class="stat-icon">📈</div>
          <div class="stat-content">
            <div class="stat-value">${{ formatFunding(stats.avgFunding) }}</div>
            <div class="stat-label">Avg per Award</div>
          </div>
        </div>
      </div>

      <!-- Top Universities Section -->
      <div class="top-section">
        <div class="section-header">
          <h3>🔝 Top Universities</h3>
          <div class="toggle-buttons">
            <button
              :class="{ active: topView === 'funding' }"
              @click="topView = 'funding'"
            >
              By Funding
            </button>
            <button
              :class="{ active: topView === 'awards' }"
              @click="topView = 'awards'"
            >
              By Awards
            </button>
          </div>
        </div>

        <div class="top-list">
          <div
            v-for="(uni, idx) in topUniversities"
            :key="uni.institution"
            class="top-item"
            @click="$emit('select-university', uni.institution)"
          >
            <div class="rank">{{ idx + 1 }}</div>
            <div class="uni-info">
              <div class="uni-name">{{ uni.institution }}</div>
              <div class="uni-location">{{ uni.city }}, {{ uni.region }}</div>
            </div>
            <div class="uni-stats">
              <div class="primary-stat">
                {{
                  topView === "funding"
                    ? `$${formatFunding(uni.total_funding)}`
                    : `${uni.award_count} awards`
                }}
              </div>
              <div class="secondary-stat">
                {{
                  topView === "funding"
                    ? `${uni.award_count} awards`
                    : `$${formatFunding(uni.total_funding)}`
                }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from "vue";
import axios from "axios";

const emit = defineEmits(["select-university"]);

const isCollapsed = ref(false);

const stats = ref({
  universityCount: null as number | null,
  professorCount: null as number | null,
  awardCount: null as number | null,
  totalFunding: null as number | null,
  avgFunding: null as number | null,
});

const topView = ref<"funding" | "awards">("funding");
const topUniversities = ref<any[]>([]);

function formatFunding(amount: number | null | undefined): string {
  if (!amount) return "0";

  if (amount >= 1e9) {
    return (amount / 1e9).toFixed(2) + "B";
  } else if (amount >= 1e6) {
    return (amount / 1e6).toFixed(2) + "M";
  } else if (amount >= 1e3) {
    return (amount / 1e3).toFixed(2) + "K";
  }
  return amount.toFixed(2);
}

async function fetchStats() {
  try {
    const [universityRes, professorRes, awardRes, fundingRes, avgRes] =
      await Promise.all([
        axios.get("/api/stats/university-count"),
        axios.get("/api/stats/professor-count"),
        axios.get("/api/stats/award-count"),
        axios.get("/api/stats/funding-total"),
        axios.get("/api/stats/avg-funding-per-award"),
      ]);

    stats.value = {
      universityCount: universityRes.data.count,
      professorCount: professorRes.data.count,
      awardCount: awardRes.data.count,
      totalFunding: fundingRes.data.total_funding,
      avgFunding: avgRes.data.avg_funding,
    };
  } catch (err) {
    console.error("Failed to fetch stats:", err);
  }
}

async function fetchTopUniversities() {
  try {
    const endpoint =
      topView.value === "funding"
        ? "/api/universities/top-funded?limit=10"
        : "/api/universities/most-awards?limit=10";

    const res = await axios.get(endpoint);
    topUniversities.value = res.data;
  } catch (err) {
    console.error("Failed to fetch top universities:", err);
  }
}

watch(topView, () => {
  fetchTopUniversities();
});

onMounted(() => {
  fetchStats();
  fetchTopUniversities();
});
</script>

<style scoped>
.stats-dashboard {
  padding: 24px;
  background: #f8fafc;
  border-radius: 12px;
  margin-bottom: 24px;
  transition: all 0.3s ease;
}

.stats-dashboard.collapsed {
  padding: 16px 24px;
  margin-bottom: 8px;
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.stats-dashboard.collapsed .dashboard-header {
  margin-bottom: 0;
}

h2 {
  margin: 0;
  font-size: 24px;
  color: #1e293b;
}

.toggle-btn {
  padding: 8px 16px;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  color: #64748b;
}

.toggle-btn:hover {
  background: #f1f5f9;
  border-color: #cbd5e1;
}

.dashboard-content {
  animation: slideDown 0.3s ease;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 32px;
}

.stat-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  transition: transform 0.2s, box-shadow 0.2s;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.stat-icon {
  font-size: 32px;
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #0f172a;
  line-height: 1;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 13px;
  color: #64748b;
  font-weight: 500;
}

.top-section {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.section-header h3 {
  margin: 0;
  font-size: 18px;
  color: #1e293b;
}

.toggle-buttons {
  display: flex;
  gap: 8px;
}

.toggle-buttons button {
  padding: 8px 16px;
  border: 1px solid #e2e8f0;
  background: white;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.toggle-buttons button:hover {
  background: #f1f5f9;
}

.toggle-buttons button.active {
  background: #3b82f6;
  color: white;
  border-color: #3b82f6;
}

.top-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.top-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background: #f8fafc;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.top-item:hover {
  background: #f1f5f9;
  transform: translateX(4px);
}

.rank {
  font-size: 20px;
  font-weight: 700;
  color: #94a3b8;
  min-width: 32px;
  text-align: center;
}

.top-item:nth-child(1) .rank {
  color: #fbbf24;
}
.top-item:nth-child(2) .rank {
  color: #94a3b8;
}
.top-item:nth-child(3) .rank {
  color: #cd7f32;
}

.uni-info {
  flex: 1;
}

.uni-name {
  font-weight: 600;
  color: #0f172a;
  margin-bottom: 2px;
}

.uni-location {
  font-size: 12px;
  color: #64748b;
}

.uni-stats {
  text-align: right;
}

.primary-stat {
  font-size: 16px;
  font-weight: 700;
  color: #0f172a;
}

.secondary-stat {
  font-size: 12px;
  color: #64748b;
}
</style>
