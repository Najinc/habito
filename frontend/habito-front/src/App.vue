<script setup lang="ts">
import AdvisorPanel from "./components/AdvisorPanel.vue";
import ResultsList from "./components/ResultsList.vue";
import { cityOptions, useSearch } from "./composables/useSearch";
import { ref } from "vue";
import Groq from "groq-sdk";
import { Mic } from "@lucide/vue";

// Initialize the Groq client
const groq = new Groq();
const isRecording = ref(false);
const recorder = ref<MediaRecorder | null>(null);
async function saveVoice() {
let chunks: BlobPart[] = [];
if(!recorder.value) {
  const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  recorder.value = new MediaRecorder(stream);
}

if(isRecording.value) {
  recorder.value.stop();
  isRecording.value = false;
  return;
}

isRecording.value = true;
recorder.value.ondataavailable = (event) => {
  chunks.push(event.data);
};

recorder.value.onstop = async () => {
  const audioBlob = new Blob(chunks, { type: "audio/webm" });
  const audioFile = new File([audioBlob], "recording.webm", { type: audioBlob.type });

  console.log(audioBlob);
  const transcription = await groq.audio.transcriptions.create({
    file: audioFile,
    model: "whisper-large-v3-turbo",
    language: "fr",
  });

  console.log(transcription);
};
recorder.value.start();
}

const {
  query,
  searchCity,
  isLoading,
  errorMessage,
  successMessage,
  allResults,
  results,
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
  search,
  askAdvisor,
} = useSearch();
</script>

<template>
  <main class="min-h-screen bg-gradient-to-br from-sky-100 via-slate-100 to-emerald-100 px-4 py-10">
    <div class="mx-auto w-full max-w-7xl">
      <div class="grid gap-6">
        <section class="space-y-6 rounded-3xl bg-white/85 p-6 shadow-soft backdrop-blur md:p-10">
          <header class="space-y-2">
            <p class="inline-flex rounded-full bg-sky-100 px-3 py-1 text-sm font-medium text-sky-800">
              Habito - Moteur immobilier assisté
            </p>
            <h1 class="text-3xl font-bold text-slate-900 md:text-4xl">
              Trouve rapidement les meilleures annonces
            </h1>
            <p class="text-slate-600">
              Recherche par ville, filtres metier et recommandation conversationnelle en temps réel.
            </p>
          </header>

          <form class="space-y-4" @submit.prevent="search">
            <label class="block text-sm font-semibold text-slate-700" for="query">Ta recherche</label>
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
                <option v-for="city in cityOptions" :key="city" :value="city">{{ city }}</option>
              </select>
              <button
                type="submit"
                :disabled="isLoading"
                class="h-12 rounded-xl bg-sky-700 px-6 font-semibold text-white transition hover:bg-sky-600 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {{ isLoading ? "Recherche en cours..." : "Lancer la recherche" }}
              </button>
            </div>
            <button
                type="button"
                @click="saveVoice"
                :class="isRecording ? 'h-12 rounded-xl bg-red-600 px-6 font-semibold text-white transition hover:bg-red-500 disabled:cursor-not-allowed disabled:opacity-60' : 'h-12 rounded-xl bg-green-600 px-6 font-semibold text-white transition hover:bg-green-500 disabled:cursor-not-allowed disabled:opacity-60'"
              >
                <Mic />
              </button>
          </form>

          <p
            v-if="successMessage"
            class="rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800"
          >
            {{ successMessage }}
          </p>

          <p
            v-if="errorMessage"
            class="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700"
          >
            {{ errorMessage }}
          </p>

          <section class="space-y-4 rounded-2xl bg-slate-50 p-4 md:p-5">
            <h3 class="text-sm font-semibold text-slate-700">Filtrer les resultats</h3>
            <div class="grid gap-4 md:grid-cols-3 lg:grid-cols-6">
              <div class="space-y-1">
                <label class="text-xs font-medium text-slate-600">Prix min (EUR)</label>
                <input
                  v-model="filters.minPrice"
                  type="number"
                  placeholder="Min"
                  class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 outline-none transition focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100"
                  @change="applyFilters"
                />
              </div>
              <div class="space-y-1">
                <label class="text-xs font-medium text-slate-600">Prix max (EUR)</label>
                <input
                  v-model="filters.maxPrice"
                  type="number"
                  placeholder="Max"
                  class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 outline-none transition focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100"
                  @change="applyFilters"
                />
              </div>

              <div class="space-y-1">
                <label class="text-xs font-medium text-slate-600">Surface min (m2)</label>
                <input
                  v-model="filters.minSquare"
                  type="number"
                  placeholder="Min"
                  class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 outline-none transition focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100"
                  @change="applyFilters"
                />
              </div>
              <div class="space-y-1">
                <label class="text-xs font-medium text-slate-600">Surface max (m2)</label>
                <input
                  v-model="filters.maxSquare"
                  type="number"
                  placeholder="Max"
                  class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 outline-none transition focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100"
                  @change="applyFilters"
                />
              </div>

              <div class="space-y-1">
                <label class="text-xs font-medium text-slate-600">Pieces min</label>
                <input
                  v-model="filters.minRooms"
                  type="number"
                  placeholder="Min"
                  class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 outline-none transition focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100"
                  @change="applyFilters"
                />
              </div>

              <div class="space-y-1">
                <label class="text-xs font-medium text-slate-600">Score min</label>
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

        <div class="grid gap-6 lg:grid-cols-3">
          <div class="lg:col-span-2">
            <ResultsList
              :results="results"
              :all-results-count="allResults.length"
              :has-results="hasResults"
              :is-loading="isLoading"
              :format-price="formatPrice"
              :short-text="shortText"
              :score-style="scoreStyle"
            />
          </div>

          <div class="lg:col-span-1">
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
        </div>
      </div>
    </div>
  </main>
</template>
