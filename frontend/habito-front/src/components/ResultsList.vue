<script setup lang="ts">
import { ref, onMounted, watch } from "vue";
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
}

const props = defineProps<Props>();
const emit = defineEmits<{
  loadMore: [];
}>();

const observerTarget = ref<HTMLDivElement | null>(null);
const isLoadingMore = ref(false);

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
          <div class="h-40 w-full flex-shrink-0 md:w-40">
            <img
              v-if="item.payload.image_url"
              :src="item.payload.image_url"
              :alt="item.payload.subject || 'Photo annonce'"
              class="h-full w-full rounded-lg object-cover"
              onerror="this.style.display = 'none'"
            />
            <div
              v-else
              class="flex h-full w-full items-center justify-center rounded-lg bg-slate-200 text-sm text-slate-400"
            >
              Pas d'image
            </div>
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
                  <span
                    class="whitespace-nowrap rounded-lg border px-2 py-1 font-medium"
                    :style="scoreStyle(item.score)"
                  >
                    Score {{ item.score.toFixed(2) }}
                  </span>
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

            <a
              v-if="item.payload.url"
              :href="item.payload.url"
              target="_blank"
              rel="noreferrer"
              class="mt-4 inline-flex text-sm font-semibold text-indigo-600 hover:text-indigo-500"
            >
              Voir l'annonce ->
            </a>
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
  </section>
</template>
