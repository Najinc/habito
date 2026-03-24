<script setup lang="ts">
import { ref, onMounted, watch, computed } from "vue";
import ImageGallery from "./ImageGallery.vue";
import ScoreBreakdown from "./ScoreBreakdown.vue";
import DetailModal from "./DetailModal.vue";
import ComparatorView from "./ComparatorView.vue";
import type { SearchResult } from "../types/search";

interface Props {
  results: SearchResult[];
  allResultsCount: number;
  hasResults: boolean;
  isLoading: boolean;
  hasMoreResults: boolean;
  formatPrice: (value?: number | null) => string;
  shortText: (value?: string | null) => string;
  scoreStyle: (score: number) => Record<string, string>;
  selectedForComparison: Set<string>;
  toggleSelection: (url: string) => void;
  clearSelection: () => void;
}

const props = defineProps<Props>();
const emit = defineEmits<{
  loadMore: [];
}>();

const observerTarget = ref<HTMLDivElement | null>(null);
const isLoadingMore = ref(false);
const selectedResult = ref<SearchResult | null>(null);
const isDetailModalOpen = ref(false);
const showComparator = ref(false);

const selectedResults = computed(() => {
  return props.results.filter((r) =>
    props.selectedForComparison.has(r.payload.url || ""),
  );
});

const openDetailModal = (result: SearchResult) => {
  selectedResult.value = result;
  isDetailModalOpen.value = true;
};

const closeDetailModal = () => {
  isDetailModalOpen.value = false;
  selectedResult.value = null;
};

onMounted(() => {
  const observer = new IntersectionObserver(
    (entries) => {
      if (
        entries[0].isIntersecting &&
        props.hasMoreResults &&
        !isLoadingMore.value
      ) {
        isLoadingMore.value = true;
        emit("loadMore");
        // Delay to prevent multiple triggers
        setTimeout(() => {
          isLoadingMore.value = false;
        }, 300);
      }
    },
    { threshold: 0.1 },
  );

  if (observerTarget.value) {
    observer.observe(observerTarget.value);
  }

  watch(
    () => props.hasResults,
    () => {
      if (observerTarget.value) {
        observer.observe(observerTarget.value);
      }
    },
  );
});
</script>

<template>
  <section class="space-y-4 rounded-3xl bg-white/90 p-5 shadow-soft md:p-7">
    <div class="flex items-center justify-between">
      <h2 class="text-2xl font-bold text-slate-900">Resultats</h2>
      <span
        class="rounded-full bg-slate-100 px-3 py-1 text-sm font-medium text-slate-600"
      >
        <span v-if="allResultsCount > 0">
          Affichage {{ results.length }} / {{ allResultsCount }}
        </span>
        <span v-else>0 annonce(s)</span>
      </span>
    </div>

    <div
      v-if="!hasResults && !isLoading"
      class="rounded-xl border border-dashed border-slate-300 bg-slate-50 p-8 text-center text-slate-500"
    >
      Lance une requete pour afficher les annonces ici.
    </div>

    <ul v-else class="grid gap-4">
      <li
        v-for="(item, index) in results"
        :key="item.payload.url ?? `result-${index}`"
        class="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm transition hover:shadow-md"
      >
        <div class="flex flex-col gap-4 p-5 md:flex-row">
          <!-- Checkbox for comparison -->
          <div class="flex items-start">
            <input
              type="checkbox"
              :checked="selectedForComparison.has(item.payload.url || '')"
              @change="toggleSelection(item.payload.url || '')"
              class="h-5 w-5 cursor-pointer rounded border-slate-300 text-indigo-600 transition focus:ring-indigo-500"
              :disabled="
                !selectedForComparison.has(item.payload.url || '') &&
                selectedForComparison.size >= 3
              "
            />
          </div>

          <div class="flex-shrink-0 md:w-64">
            <ImageGallery
              :images="item.payload.images"
              :title="item.payload.subject || 'Photos annonce'"
            />
          </div>

          <div class="flex flex-1 flex-col">
            <div class="flex flex-1 flex-col gap-3">
              <div class="flex items-start justify-between gap-2">
                <div class="flex-1 space-y-2">
                  <h3 class="text-lg font-semibold text-slate-900">
                    {{ item.payload.subject || "Annonce sans titre" }}
                  </h3>
                  <p class="text-sm text-slate-600">
                    {{ shortText(item.payload.body) }}
                  </p>
                </div>
                <div class="flex-shrink-0 text-sm">
                  <ScoreBreakdown
                    :score="item.score"
                    :breakdown="item.payload.score_breakdown"
                  />
                </div>
              </div>

              <div class="flex flex-wrap gap-2 text-sm text-slate-600">
                <span class="rounded-lg bg-slate-100 px-2 py-1">{{
                  formatPrice(item.payload.price)
                }}</span>
                <span class="rounded-lg bg-slate-100 px-2 py-1">{{
                  item.payload.city || "Ville non renseignee"
                }}</span>
                <span
                  v-if="item.payload.square"
                  class="rounded-lg bg-slate-100 px-2 py-1"
                  >{{ item.payload.square }} m2</span
                >
                <span
                  v-if="item.payload.rooms"
                  class="rounded-lg bg-slate-100 px-2 py-1"
                  >{{ item.payload.rooms }} piece(s)</span
                >
              </div>
            </div>

            <div class="mt-4 flex flex-wrap gap-2">
              <button
                @click="openDetailModal(item)"
                class="inline-flex text-sm font-semibold text-indigo-600 transition hover:text-indigo-500"
              >
                📄 Voir les détails
              </button>
              <a
                v-if="item.payload.url"
                :href="item.payload.url"
                target="_blank"
                rel="noreferrer"
                class="inline-flex text-sm font-semibold text-slate-600 transition hover:text-slate-500"
              >
                Voir sur LBC →
              </a>
            </div>
          </div>
        </div>
      </li>

      <!-- Scroll infini - Observer element -->
      <li
        v-if="hasMoreResults || isLoading"
        ref="observerTarget"
        class="flex justify-center py-8"
      >
        <div v-if="isLoading" class="flex items-center gap-2 text-slate-600">
          <div
            class="h-4 w-4 animate-spin rounded-full border-2 border-indigo-500 border-t-transparent"
          ></div>
          <span class="text-sm">Chargement plus d'annonces...</span>
        </div>
        <span v-else class="text-sm text-slate-500"
          >↓ Scroll pour charger plus</span
        >
      </li>
    </ul>

    <!-- Detail Modal -->
    <DetailModal
      :is-open="isDetailModalOpen"
      :result="selectedResult"
      :format-price="formatPrice"
      @close="closeDetailModal"
    />

    <!-- Comparator button (sticky) -->
    <div
      v-if="selectedForComparison.size > 0"
      class="fixed bottom-6 right-6 z-30 flex items-center gap-3 rounded-lg bg-indigo-600 px-4 py-3 shadow-lg"
    >
      <div class="flex items-center gap-2 text-white">
        <svg
          class="h-5 w-5"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
          />
        </svg>
        <span class="text-sm font-semibold"
          >{{ selectedForComparison.size }} sélectionné(e)</span
        >
      </div>
      <button
        @click="showComparator = true"
        class="rounded-lg bg-white px-3 py-1 text-sm font-semibold text-indigo-600 transition hover:bg-indigo-50"
      >
        Comparer
      </button>
      <button
        @click="clearSelection"
        class="rounded-lg text-white/80 transition hover:text-white"
      >
        <svg
          class="h-5 w-5"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M6 18L18 6M6 6l12 12"
          />
        </svg>
      </button>
    </div>

    <!-- Comparator View -->
    <ComparatorView
      v-if="showComparator"
      :selected-results="selectedResults"
      :format-price="formatPrice"
      @close="showComparator = false"
    />
  </section>
</template>
