<script setup lang="ts">
import { ref } from "vue";

interface ScoreBreakdown {
  vector_score: number;
  rerank_score?: number;
  city_boost: number;
  date_boost: number;
  image_boost: number;
  verified_boost: number;
  total_score: number;
}

interface Props {
  score: number;
  breakdown?: ScoreBreakdown | null;
}

const props = defineProps<Props>();
const isOpen = ref(false);

const togglePopover = () => {
  isOpen.value = !isOpen.value;
};

const getBoostColor = (value: number) => {
  if (value > 0.3) return "text-green-600";
  if (value > 0.1) return "text-emerald-600";
  if (value > 0) return "text-lime-600";
  return "text-slate-400";
};
</script>

<template>
  <div class="relative">
    <!-- Score badge with info icon -->
    <button
      @click="togglePopover"
      class="group relative inline-flex items-center gap-2 whitespace-nowrap rounded-lg border px-2 py-1 font-medium transition"
      :style="{
        backgroundImage: `linear-gradient(135deg, hsl(${Math.min(130, (score / 4) * 130)} 85% 92%), hsl(${Math.min(130, (score / 4) * 130)} 70% 80%))`,
        color: '#0f172a',
        borderColor: `hsl(${Math.min(130, (score / 4) * 130)} 45% 62%)`,
      }"
    >
      <span class="text-sm">Score {{ score.toFixed(2) }}</span>
      <svg
        v-if="breakdown"
        class="h-4 w-4 transition group-hover:scale-110"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
        />
      </svg>
    </button>

    <!-- Popover -->
    <transition
      enter-active-class="transition duration-200"
      enter-from-class="opacity-0 scale-95"
      enter-to-class="opacity-100 scale-100"
      leave-active-class="transition duration-150"
      leave-from-class="opacity-100 scale-100"
      leave-to-class="opacity-0 scale-95"
    >
      <div
        v-if="isOpen && breakdown"
        class="absolute right-0 top-full z-40 mt-2 w-72 origin-top-right rounded-lg border border-slate-200 bg-white shadow-lg"
      >
        <!-- Header -->
        <div
          class="border-b border-slate-200 bg-gradient-to-r from-indigo-50 to-blue-50 px-4 py-3"
        >
          <h3 class="text-sm font-semibold text-slate-900">Détail du Score</h3>
          <p class="mt-1 text-xs text-slate-600">Pourquoi ce score?</p>
        </div>

        <!-- Scores breakdown -->
        <div class="space-y-3 px-4 py-3">
          <!-- Vector Score -->
          <div class="flex items-center justify-between gap-2 text-sm">
            <span class="text-slate-700">Score vector (sémantique)</span>
            <span
              class="rounded bg-slate-100 px-2 py-1 font-mono text-slate-900"
            >
              {{ breakdown.vector_score.toFixed(3) }}
            </span>
          </div>

          <!-- Rerank Score -->
          <div
            v-if="breakdown.rerank_score !== undefined"
            class="flex items-center justify-between gap-2 text-sm"
          >
            <span class="text-slate-700">Score rerank</span>
            <span
              class="rounded bg-slate-100 px-2 py-1 font-mono text-slate-900"
            >
              {{ breakdown.rerank_score.toFixed(3) }}
            </span>
          </div>

          <div class="border-t border-slate-200 pt-2">
            <p class="mb-2 text-xs font-medium text-slate-600">
              Boosts appliqués:
            </p>

            <!-- City Boost -->
            <div class="flex items-center justify-between gap-2 text-xs">
              <span class="text-slate-600">📍 Localisation</span>
              <span :class="getBoostColor(breakdown.city_boost)">
                {{ breakdown.city_boost > 0 ? "+" : ""
                }}{{ breakdown.city_boost.toFixed(3) }}
              </span>
            </div>

            <!-- Date Boost -->
            <div class="flex items-center justify-between gap-2 text-xs">
              <span class="text-slate-600">📅 Date publication</span>
              <span :class="getBoostColor(breakdown.date_boost)">
                {{ breakdown.date_boost > 0 ? "+" : ""
                }}{{ breakdown.date_boost.toFixed(3) }}
              </span>
            </div>

            <!-- Image Boost -->
            <div class="flex items-center justify-between gap-2 text-xs">
              <span class="text-slate-600">🖼️ Nombre photos</span>
              <span :class="getBoostColor(breakdown.image_boost)">
                {{ breakdown.image_boost > 0 ? "+" : ""
                }}{{ breakdown.image_boost.toFixed(3) }}
              </span>
            </div>

            <!-- Verified Boost -->
            <div class="flex items-center justify-between gap-2 text-xs">
              <span class="text-slate-600">✓ Verified/PRO</span>
              <span :class="getBoostColor(breakdown.verified_boost)">
                {{ breakdown.verified_boost > 0 ? "+" : ""
                }}{{ breakdown.verified_boost.toFixed(3) }}
              </span>
            </div>
          </div>

          <!-- Total Score -->
          <div class="border-t border-slate-200 pt-2">
            <div
              class="flex items-center justify-between gap-2 rounded-lg bg-indigo-50 px-2 py-2 text-sm font-semibold"
            >
              <span class="text-indigo-900">Score final</span>
              <span class="font-mono text-indigo-900">{{
                breakdown.total_score.toFixed(3)
              }}</span>
            </div>
          </div>
        </div>

        <!-- Footer -->
        <div class="border-t border-slate-200 bg-slate-50 px-4 py-2">
          <p class="text-xs text-slate-500">
            Plus de détails = meilleur classement
          </p>
        </div>
      </div>
    </transition>

    <!-- Close button on backdrop -->
    <div v-if="isOpen" @click="isOpen = false" class="fixed inset-0 z-30" />
  </div>
</template>
