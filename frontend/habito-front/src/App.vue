<script setup lang="ts">
import { computed, ref } from "vue";

type SearchPayload = {
  ad_id?: string | null;
  subject?: string | null;
  body?: string | null;
  price?: number | null;
  city?: string | null;
  square?: number | null;
  rooms?: number | null;
  url?: string | null;
  image_url?: string | null;
  source?: string | null;
};

type SearchResult = {
  score: number;
  payload: SearchPayload;
};

const query = ref("appartement Lille");
const isLoading = ref(false);
const errorMessage = ref("");
const results = ref<SearchResult[]>([]);

const hasResults = computed(() => results.value.length > 0);

const formatPrice = (value?: number | null): string => {
  if (typeof value !== "number") return "Prix non renseigné";
  return new Intl.NumberFormat("fr-FR", {
    style: "currency",
    currency: "EUR",
    maximumFractionDigits: 0,
  }).format(value);
};

const shortText = (text?: string | null): string => {
  if (!text) return "Description non disponible.";
  return text.length > 240 ? `${text.slice(0, 240)}…` : text;
};

const scoreStyle = (score: number): Record<string, string> => {
  const clampedScore = Math.max(0, Math.min(4, score));
  const normalizedScore = clampedScore / 4;
  const hue = Math.round(normalizedScore * 120);
  const startHue = Math.max(0, hue - 16);
  const endHue = Math.min(130, hue + 8);

  return {
    backgroundImage: `linear-gradient(135deg, hsl(${startHue} 85% 92%), hsl(${endHue} 70% 80%))`,
    color: "#0f172a",
    borderColor: `hsl(${endHue} 45% 62%)`,
  };
};

const search = async () => {
  const cleanQuery = query.value.trim();
  if (!cleanQuery) {
    errorMessage.value = "Saisis une recherche avant de lancer le test.";
    return;
  }

  isLoading.value = true;
  errorMessage.value = "";

  try {
    const response = await fetch("http://localhost:8000/api/search", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ query: cleanQuery }),
    });

    if (!response.ok) {
      const body = await response.text();
      throw new Error(body || `Erreur HTTP ${response.status}`);
    }

    const data = (await response.json()) as SearchResult[];
    results.value = Array.isArray(data) ? data : [];
  } catch (error) {
    results.value = [];
    errorMessage.value =
      error instanceof Error ? error.message : "Erreur inconnue.";
  } finally {
    isLoading.value = false;
  }
};
</script>

<template>
  <main
    class="min-h-screen bg-gradient-to-br from-indigo-100 via-slate-100 to-cyan-100 px-4 py-10"
  >
    <div class="mx-auto w-full max-w-7xl">
      <div class="grid gap-6 lg:grid-cols-1">
        <!-- Search Section -->
        <section
          class="space-y-6 rounded-3xl bg-white/80 p-6 shadow-soft backdrop-blur md:p-10"
        >
          <header class="space-y-2">
            <p
              class="inline-flex rounded-full bg-indigo-50 px-3 py-1 text-sm font-medium text-indigo-700"
            >
              Habito • Recherche immobiliere intelligente
            </p>
            <h1 class="text-3xl font-bold text-slate-900 md:text-4xl">
              Trouve rapidement des annonces immobilières
            </h1>
            <p class="text-slate-600">
              Interface de recherche avec retrieval semantique et reranking pour
              des resultats plus pertinents.
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
                placeholder="Ex: appartement Lille, studio Paris..."
                class="h-12 flex-1 rounded-xl border border-slate-200 bg-white px-4 text-slate-900 shadow-sm outline-none ring-indigo-300 transition focus:border-indigo-400 focus:ring-4"
              />
              <button
                type="submit"
                :disabled="isLoading"
                class="h-12 rounded-xl bg-indigo-600 px-6 font-semibold text-white transition hover:bg-indigo-500 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {{ isLoading ? "Recherche en cours…" : "Lancer la recherche" }}
              </button>
            </div>
          </form>

          <p
            v-if="errorMessage"
            class="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700"
          >
            {{ errorMessage }}
          </p>

          <section class="space-y-4">
            <div class="flex items-center justify-between">
              <h2 class="text-xl font-semibold text-slate-900">Résultats</h2>
              <span
                class="rounded-full bg-slate-100 px-3 py-1 text-sm font-medium text-slate-600"
              >
                {{ results.length }} annonce(s)
              </span>
            </div>

            <div
              v-if="!hasResults && !isLoading"
              class="rounded-xl border border-dashed border-slate-300 bg-slate-50 p-8 text-center text-slate-500"
            >
              Lance une requête pour afficher les annonces ici.
            </div>

            <ul v-else class="grid gap-4">
              <li
                v-for="(item, index) in results"
                :key="item.payload.url ?? `result-${index}`"
                class="rounded-2xl border border-slate-200 bg-white shadow-sm transition hover:shadow-md overflow-hidden"
              >
                <div class="flex flex-col md:flex-row gap-4 p-5">
                  <!-- Image -->
                  <div class="flex-shrink-0 w-full md:w-40 h-40">
                    <img
                      v-if="item.payload.image_url"
                      :src="item.payload.image_url"
                      :alt="item.payload.subject || 'Photo annonce'"
                      class="w-full h-full object-cover rounded-lg"
                      onerror="this.style.display = 'none'"
                    />
                    <div
                      v-else
                      class="w-full h-full bg-slate-200 rounded-lg flex items-center justify-center text-slate-400 text-sm"
                    >
                      Pas d'image
                    </div>
                  </div>

                  <!-- Content -->
                  <div class="flex-1 flex flex-col">
                    <div class="flex flex-col gap-3 flex-1">
                      <div class="flex items-start justify-between gap-2">
                        <div class="space-y-2 flex-1">
                          <h3 class="text-lg font-semibold text-slate-900">
                            {{ item.payload.subject || "Annonce sans titre" }}
                          </h3>
                          <p class="text-sm text-slate-600">
                            {{ shortText(item.payload.body) }}
                          </p>
                        </div>
                        <div class="flex-shrink-0 text-sm">
                          <span
                            class="rounded-lg border px-2 py-1 font-medium whitespace-nowrap"
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
                          item.payload.city || "Ville non renseignée"
                        }}</span>
                        <span class="rounded-lg bg-slate-100 px-2 py-1"
                          >{{ item.payload.square ?? "N/A" }} m²</span
                        >
                        <span class="rounded-lg bg-slate-100 px-2 py-1"
                          >{{ item.payload.rooms ?? "N/A" }} pièce(s)</span
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
                      Voir l'annonce →
                    </a>
                  </div>
                </div>
              </li>
            </ul>
          </section>
        </section>
      </div>
    </div>
  </main>
</template>
