<script setup lang="ts">
import ImageGallery from "./ImageGallery.vue";
import type { SearchResult } from "../types/search";

interface Props {
  isOpen: boolean;
  result?: SearchResult | null;
  formatPrice: (value?: number | null) => string;
}

const props = defineProps<Props>();
const emit = defineEmits<{
  close: [];
}>();

const handleBackdropClick = () => {
  emit("close");
};

const handleEscapeKey = (e: KeyboardEvent) => {
  if (e.key === "Escape") {
    emit("close");
  }
};

const formatDate = (timestamp?: number | null): string => {
  if (!timestamp) return "Date inconnue";
  try {
    const date = new Date(timestamp * 1000);
    return new Intl.DateTimeFormat("fr-FR", {
      year: "numeric",
      month: "long",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    }).format(date);
  } catch {
    return "Date non disponible";
  }
};

const getOwnerBadge = (
  ownerType?: string | null,
): { label: string; color: string } => {
  if (ownerType === "Agence") {
    return { label: "Agence", color: "bg-blue-100 text-blue-800" };
  }
  return { label: "Particulier", color: "bg-emerald-100 text-emerald-800" };
};
</script>

<template>
  <teleport to="body">
    <transition name="fade">
      <div
        v-if="isOpen && result"
        @keydown="handleEscapeKey"
        tabindex="0"
        class="fixed inset-0 z-40 flex items-center justify-center bg-slate-950/80 p-4"
      >
        <!-- Modal content -->
        <div
          @click.stop
          class="max-h-[90vh] w-full max-w-3xl overflow-y-auto rounded-2xl bg-white shadow-2xl"
        >
          <!-- Header -->
          <div
            class="sticky top-0 flex items-start justify-between border-b border-slate-200 bg-gradient-to-r from-indigo-50 to-blue-50 p-6"
          >
            <div class="flex-1 pr-4">
              <h2 class="text-2xl font-bold text-slate-900">
                {{ result.payload.subject }}
              </h2>
              <p class="mt-2 text-sm text-slate-600">
                {{ result.payload.city }}
              </p>
            </div>
            <button
              @click="handleBackdropClick"
              class="flex-shrink-0 rounded-lg text-slate-400 transition hover:bg-slate-200 hover:text-slate-600"
            >
              <svg
                class="h-6 w-6"
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

          <!-- Content -->
          <div class="space-y-6 p-6">
            <!-- Gallery section -->
            <div>
              <h3 class="mb-3 text-lg font-semibold text-slate-900">Photos</h3>
              <ImageGallery
                :images="result.payload.images"
                :title="result.payload.subject || 'Photos annonce'"
                :inDetailView="true"
              />
            </div>

            <!-- Key details grid -->
            <div class="grid gap-4 md:grid-cols-2">
              <!-- Price -->
              <div class="rounded-lg border border-slate-200 bg-slate-50 p-4">
                <p class="text-xs font-medium text-slate-600">PRIX</p>
                <p class="mt-1 text-2xl font-bold text-slate-900">
                  {{ formatPrice(result.payload.price) }}
                </p>
              </div>

              <!-- Surface -->
              <div
                v-if="result.payload.square"
                class="rounded-lg border border-slate-200 bg-slate-50 p-4"
              >
                <p class="text-xs font-medium text-slate-600">SURFACE</p>
                <p class="mt-1 text-2xl font-bold text-slate-900">
                  {{ result.payload.square }} m²
                </p>
              </div>

              <!-- Rooms -->
              <div
                v-if="result.payload.rooms"
                class="rounded-lg border border-slate-200 bg-slate-50 p-4"
              >
                <p class="text-xs font-medium text-slate-600">PIÈCES</p>
                <p class="mt-1 text-2xl font-bold text-slate-900">
                  {{ result.payload.rooms }} pièce(s)
                </p>
              </div>

              <!-- Views -->
              <div
                v-if="result.payload.nb_views"
                class="rounded-lg border border-slate-200 bg-slate-50 p-4"
              >
                <p class="text-xs font-medium text-slate-600">VUES</p>
                <p class="mt-1 text-2xl font-bold text-slate-900">
                  {{ result.payload.nb_views }}
                </p>
              </div>
            </div>

            <!-- Metadata section -->
            <div class="flex flex-wrap gap-2">
              <!-- Owner type -->
              <span
                :class="{
                  'rounded-full px-3 py-1 text-sm font-medium': true,
                  ...getOwnerBadge(result.payload.owner_type),
                }"
              >
                {{ result.payload.owner_type || "Particulier" }}
              </span>

              <!-- Publication date -->
              <span
                v-if="result.payload.first_publication_date"
                class="rounded-full bg-slate-100 px-3 py-1 text-sm font-medium text-slate-700"
              >
                📅 {{ formatDate(result.payload.first_publication_date) }}
              </span>

              <!-- Seniority -->
              <span
                v-if="result.payload.seniority"
                class="rounded-full bg-amber-100 px-3 py-1 text-sm font-medium text-amber-800"
              >
                ⏱️ {{ result.payload.seniority }}
              </span>

              <!-- Has phone -->
              <span
                v-if="result.payload.has_phone"
                class="rounded-full bg-green-100 px-3 py-1 text-sm font-medium text-green-800"
              >
                ☎️ Téléphone disponible
              </span>
            </div>

            <!-- Full description -->
            <div>
              <h3 class="mb-3 text-lg font-semibold text-slate-900">
                Description complète
              </h3>
              <div class="rounded-lg border border-slate-200 bg-slate-50 p-4">
                <p class="whitespace-pre-wrap text-sm text-slate-700">
                  {{ result.payload.body || "Pas de description disponible." }}
                </p>
              </div>
            </div>

            <!-- Score breakdown (if available) -->
            <div
              v-if="result.payload.score_breakdown"
              class="border-t border-slate-200 pt-6"
            >
              <h3 class="mb-3 text-lg font-semibold text-slate-900">
                Pourquoi ce score?
              </h3>
              <div class="grid gap-2 md:grid-cols-3">
                <div class="rounded-lg bg-slate-50 p-3 text-sm">
                  <p class="text-slate-600">Vector</p>
                  <p class="font-mono font-bold text-slate-900">
                    {{ result.payload.score_breakdown.vector_score.toFixed(3) }}
                  </p>
                </div>
                <div class="rounded-lg bg-slate-50 p-3 text-sm">
                  <p class="text-slate-600">Date</p>
                  <p class="font-mono font-bold text-slate-900">
                    {{ result.payload.score_breakdown.date_boost.toFixed(3) }}
                  </p>
                </div>
                <div class="rounded-lg bg-slate-50 p-3 text-sm">
                  <p class="text-slate-600">Photos</p>
                  <p class="font-mono font-bold text-slate-900">
                    {{ result.payload.score_breakdown.image_boost.toFixed(3) }}
                  </p>
                </div>
                <div class="rounded-lg bg-slate-50 p-3 text-sm">
                  <p class="text-slate-600">Lieu</p>
                  <p class="font-mono font-bold text-slate-900">
                    {{ result.payload.score_breakdown.city_boost.toFixed(3) }}
                  </p>
                </div>
                <div class="rounded-lg bg-slate-50 p-3 text-sm">
                  <p class="text-slate-600">Verified</p>
                  <p class="font-mono font-bold text-slate-900">
                    {{
                      result.payload.score_breakdown.verified_boost.toFixed(3)
                    }}
                  </p>
                </div>
                <div class="rounded-lg bg-indigo-50 p-3 text-sm font-bold">
                  <p class="text-indigo-600">Total</p>
                  <p class="font-mono text-indigo-900">
                    {{ result.payload.score_breakdown.total_score.toFixed(3) }}
                  </p>
                </div>
              </div>
            </div>
          </div>

          <!-- Footer -->
          <div class="flex gap-3 border-t border-slate-200 bg-slate-50 p-6">
            <button
              @click="handleBackdropClick"
              class="flex-1 rounded-lg border border-slate-300 bg-white px-4 py-2 font-semibold text-slate-900 transition hover:bg-slate-100"
            >
              Fermer
            </button>
            <a
              v-if="result.payload.url"
              :href="result.payload.url"
              target="_blank"
              rel="noreferrer"
              class="flex-1 rounded-lg bg-indigo-600 px-4 py-2 text-center font-semibold text-white transition hover:bg-indigo-700"
            >
              Voir sur Leboncoin →
            </a>
          </div>
        </div>
      </div>
    </transition>
  </teleport>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
