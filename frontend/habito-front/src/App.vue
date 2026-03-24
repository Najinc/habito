<script setup lang="ts">
import AdvisorPanel from "./components/AdvisorPanel.vue";
import ResultsList from "./components/ResultsList.vue";
import MapView from "./components/MapView.vue";
import {
  cityOptions,
  cityCoordinates,
  useSearch,
} from "./composables/useSearch";

const {
  query,
  searchCity,
  filterRadius,
  sortBy,
  isLoading,
  errorMessage,
  allResults,
  results,
  paginatedResults,
  hasMoreResults,
  filters,
  chatQuestion,
  chatAnswer,
  chatRecommendedUrl,
  chatError,
  isChatLoading,
  hasResults,
  formatPrice,
  shortText,
  scoreStyle,
  applyFilters,
  sortResults,
  search,
  askAdvisor,
  loadMoreResults,
} = useSearch();

const getCityCoordinates = (city: string) => {
  return cityCoordinates[city] || { lat: 48.8566, lng: 2.3522 };
};

const handleRadiusUpdate = (radius: number) => {
  filterRadius.value = radius.toString();
};
</script>

<template>
  <main
    class="min-h-screen bg-gradient-to-br from-sky-100 via-slate-100 to-emerald-100 px-4 py-10"
  >
    <div class="mx-auto w-full max-w-7xl">
      <div class="grid gap-6">
        <section
          class="space-y-6 rounded-3xl bg-white/85 p-6 shadow-soft backdrop-blur md:p-10"
        >
          <header class="space-y-2">
            <p
              class="inline-flex rounded-full bg-sky-100 px-3 py-1 text-sm font-medium text-sky-800"
            >
              Habito - Moteur immobilier assisté
            </p>
            <h1 class="text-3xl font-bold text-slate-900 md:text-4xl">
              Trouve rapidement les meilleures annonces
            </h1>
            <p class="text-slate-600">
              Recherche par ville, filtres metier et recommandation
              conversationnelle en temps réel.
            </p>
          </header>

          <form class="space-y-4" @submit.prevent="search">
            <label
              class="block text-sm font-semibold text-slate-700"
              for="query"
              >Ta recherche</label
            >
            <div class="flex flex-col gap-3 md:flex-row">
              <input
                id="query"
                v-model="query"
                type="text"
                placeholder="Ex: appartement, studio..."
                class="h-12 flex-1 rounded-xl border border-slate-200 bg-white px-4 text-slate-900 shadow-sm outline-none ring-indigo-300 transition focus:border-indigo-400 focus:ring-4"
              />
              <select
                v-model="searchCity"
                class="h-12 rounded-xl border border-slate-200 bg-white px-4 text-slate-900 shadow-sm outline-none ring-indigo-300 transition focus:border-indigo-400 focus:ring-4"
              >
                <option v-for="city in cityOptions" :key="city" :value="city">
                  {{ city }}
                </option>
              </select>
              <button
                type="submit"
                :disabled="isLoading"
                class="h-12 rounded-xl bg-sky-700 px-6 font-semibold text-white transition hover:bg-sky-600 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {{
                  isLoading ? "Recherche en cours..." : "Lancer la recherche"
                }}
              </button>
            </div>
          </form>

          <p
            v-if="errorMessage"
            class="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700"
          >
            {{ errorMessage }}
          </p>

          <section class="space-y-4 rounded-2xl bg-slate-50 p-4 md:p-5">
            <h3 class="text-sm font-semibold text-slate-700">
              Filtrer les resultats
            </h3>
            <div class="grid gap-4 md:grid-cols-3 lg:grid-cols-6">
              <div class="space-y-1">
                <label class="text-xs font-medium text-slate-600"
                  >Prix min (EUR)</label
                >
                <input
                  v-model="filters.minPrice"
                  type="number"
                  placeholder="Min"
                  class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 outline-none transition focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100"
                  @change="applyFilters"
                />
              </div>
              <div class="space-y-1">
                <label class="text-xs font-medium text-slate-600"
                  >Prix max (EUR)</label
                >
                <input
                  v-model="filters.maxPrice"
                  type="number"
                  placeholder="Max"
                  class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 outline-none transition focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100"
                  @change="applyFilters"
                />
              </div>

              <div class="space-y-1">
                <label class="text-xs font-medium text-slate-600"
                  >Surface min (m2)</label
                >
                <input
                  v-model="filters.minSquare"
                  type="number"
                  placeholder="Min"
                  class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 outline-none transition focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100"
                  @change="applyFilters"
                />
              </div>
              <div class="space-y-1">
                <label class="text-xs font-medium text-slate-600"
                  >Surface max (m2)</label
                >
                <input
                  v-model="filters.maxSquare"
                  type="number"
                  placeholder="Max"
                  class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 outline-none transition focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100"
                  @change="applyFilters"
                />
              </div>

              <div class="space-y-1">
                <label class="text-xs font-medium text-slate-600"
                  >Pieces min</label
                >
                <input
                  v-model="filters.minRooms"
                  type="number"
                  placeholder="Min"
                  class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 outline-none transition focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100"
                  @change="applyFilters"
                />
              </div>

              <div class="space-y-1">
                <label class="text-xs font-medium text-slate-600"
                  >Score min</label
                >
                <input
                  v-model="filters.minScore"
                  type="number"
                  step="0.1"
                  placeholder="0.0"
                  class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 outline-none transition focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100"
                  @change="applyFilters"
                />
              </div>
            </div>
          </section>
        </section>

        <!-- Map Section -->
        <section
          class="space-y-6 rounded-3xl bg-white/85 p-6 shadow-soft backdrop-blur md:p-10"
          v-if="hasResults"
        >
          <header>
            <h2 class="text-2xl font-bold text-slate-900">
              Vue cartographique
            </h2>
          </header>
          <MapView
            :results="results"
            :search-city="searchCity"
            :city-lat="getCityCoordinates(searchCity).lat"
            :city-lng="getCityCoordinates(searchCity).lng"
            :filter-radius="filterRadius"
            @update-radius="handleRadiusUpdate"
          />
        </section>

        <div class="flex flex-col gap-6">
          <div>
            <AdvisorPanel
              :has-results="hasResults"
              :is-loading="isChatLoading"
              :question="chatQuestion"
              :answer="chatAnswer"
              :error="chatError"
              :recommended-url="chatRecommendedUrl"
              @update:question="chatQuestion = $event"
              @ask="askAdvisor"
            />
          </div>

          <!-- Sorting Section -->
          <div
            class="flex items-center justify-between rounded-3xl bg-white/85 p-6 shadow-soft backdrop-blur md:p-10"
            v-if="hasResults"
          >
            <div class="flex items-center gap-4">
              <label for="sort-by" class="text-sm font-semibold text-slate-700"
                >Trier par:</label
              >
              <select
                id="sort-by"
                v-model="sortBy"
                @change="sortResults"
                class="rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm text-slate-900 shadow-sm outline-none ring-indigo-300 transition focus:border-indigo-400 focus:ring-4"
              >
                <option value="score">Score (meilleur match)</option>
                <option value="price-asc">Prix (croissant)</option>
                <option value="price-desc">Prix (décroissant)</option>
                <option value="square-asc">Surface (croissante)</option>
                <option value="square-desc">Surface (décroissante)</option>
                <option value="newest">Plus récent</option>
              </select>
            </div>
            <p class="text-sm text-slate-600">{{ results.length }} résultats</p>
          </div>

          <div>
            <ResultsList
              :results="paginatedResults"
              :all-results-count="allResults.length"
              :has-results="hasResults"
              :is-loading="isLoading"
              :has-more-results="hasMoreResults"
              :format-price="formatPrice"
              :short-text="shortText"
              :score-style="scoreStyle"
              @load-more="loadMoreResults"
            />
          </div>
        </div>
      </div>
    </div>
  </main>
</template>
