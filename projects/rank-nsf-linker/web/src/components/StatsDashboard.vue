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
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 16px;
  margin-bottom: 16px;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 10px 40px rgba(102, 126, 234, 0.3);
}

.stats-dashboard.collapsed {
  padding: 16px 24px;
  margin-bottom: 8px;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.2);
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.stats-dashboard.collapsed .dashboard-header {
  margin-bottom: 0;
}

h2 {
  margin: 0;
  font-size: 28px;
  font-weight: 700;
  color: white;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.toggle-btn {
  padding: 10px 20px;
  background: rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  color: white;
}

.toggle-btn:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

.dashboard-content {
  animation: slideDown 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 20px;
  margin-bottom: 32px;
}

.stat-card {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 16px;
  padding: 24px;
  display: flex;
  align-items: center;
  gap: 20px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border: 1px solid rgba(255, 255, 255, 0.8);
}

.stat-card:hover {
  transform: translateY(-4px) scale(1.02);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.15);
  border-color: rgba(102, 126, 234, 0.3);
}

.stat-icon {
  font-size: 40px;
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.1));
  animation: float 3s ease-in-out infinite;
}

@keyframes float {
  0%,
  100% {
    transform: translateY(0px);
  }
  50% {
    transform: translateY(-5px);
  }
}

.stat-card:nth-child(1) .stat-icon {
  animation-delay: 0s;
}
.stat-card:nth-child(2) .stat-icon {
  animation-delay: 0.2s;
}
.stat-card:nth-child(3) .stat-icon {
  animation-delay: 0.4s;
}
.stat-card:nth-child(4) .stat-icon {
  animation-delay: 0.6s;
}
.stat-card:nth-child(5) .stat-icon {
  animation-delay: 0.8s;
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 32px;
  font-weight: 800;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  line-height: 1;
  margin-bottom: 6px;
}

.stat-label {
  font-size: 14px;
  color: #64748b;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.top-section {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 16px;
  padding: 28px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.8);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 2px solid #f1f5f9;
}

.section-header h3 {
  margin: 0;
  font-size: 20px;
  font-weight: 700;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.toggle-buttons {
  display: flex;
  gap: 8px;
  background: #f8fafc;
  padding: 4px;
  border-radius: 10px;
}

.toggle-buttons button {
  padding: 10px 18px;
  border: none;
  background: transparent;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  color: #64748b;
}

.toggle-buttons button:hover {
  background: rgba(102, 126, 234, 0.1);
  color: #667eea;
}

.toggle-buttons button.active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.top-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.top-item {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 18px;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border: 2px solid transparent;
}

.top-item:hover {
  background: linear-gradient(135deg, #fff 0%, #f8fafc 100%);
  transform: translateX(8px) scale(1.02);
  border-color: rgba(102, 126, 234, 0.3);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
}

.rank {
  font-size: 24px;
  font-weight: 800;
  color: #cbd5e1;
  min-width: 40px;
  text-align: center;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.top-item:nth-child(1) .rank {
  color: #fbbf24;
  font-size: 28px;
  animation: pulse 2s ease-in-out infinite;
}

.top-item:nth-child(2) .rank {
  color: #94a3b8;
  font-size: 26px;
}

.top-item:nth-child(3) .rank {
  color: #cd7f32;
  font-size: 26px;
}

@keyframes pulse {
  0%,
  100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.1);
  }
}

.uni-info {
  flex: 1;
}

.uni-name {
  font-weight: 700;
  font-size: 15px;
  color: #0f172a;
  margin-bottom: 4px;
}

.uni-location {
  font-size: 12px;
  color: #64748b;
  font-weight: 500;
}

.uni-stats {
  text-align: right;
}

.primary-stat {
  font-size: 18px;
  font-weight: 800;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 2px;
}

.secondary-stat {
  font-size: 12px;
  color: #94a3b8;
  font-weight: 600;
}

/* Responsive Design */
@media (max-width: 1024px) {
  .stats-grid {
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 16px;
  }

  .stat-value {
    font-size: 28px;
  }
}

@media (max-width: 768px) {
  .stats-dashboard {
    padding: 20px;
    border-radius: 12px;
  }

  h2 {
    font-size: 24px;
  }

  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
  }

  .stat-card {
    padding: 16px;
  }

  .stat-icon {
    font-size: 32px;
  }

  .stat-value {
    font-size: 24px;
  }

  .top-section {
    padding: 20px;
  }

  .section-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
}

@media (max-width: 480px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }

  .toggle-buttons {
    width: 100%;
  }

  .toggle-buttons button {
    flex: 1;
  }
}
</style>
