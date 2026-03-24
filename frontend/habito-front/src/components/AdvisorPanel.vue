<script setup lang="ts">
const props = defineProps<{
  hasResults: boolean;
  isLoading: boolean;
  question: string;
  answer: string;
  error: string;
  recommendedUrl: string;
}>();

const emit = defineEmits<{
  (e: "update:question", value: string): void;
  (e: "ask"): void;
}>();
</script>

<template>
  <section class="relative overflow-hidden rounded-3xl border border-cyan-200 bg-gradient-to-br from-cyan-50 via-white to-sky-50 p-5 shadow-soft md:p-7">
    <div class="pointer-events-none absolute -right-10 -top-10 h-40 w-40 rounded-full bg-cyan-200/40 blur-2xl"></div>
    <div class="pointer-events-none absolute -bottom-16 -left-16 h-52 w-52 rounded-full bg-sky-200/30 blur-2xl"></div>

    <div class="relative space-y-4">
      <div class="flex items-center justify-between gap-3">
        <h3 class="text-xl font-bold text-slate-900">Conseil intelligent</h3>
        <span class="rounded-full border border-cyan-300 bg-cyan-100 px-3 py-1 text-xs font-semibold text-cyan-800">
          Assistant
        </span>
      </div>

      <p class="text-sm text-slate-600">
        Obtiens une recommandation argumentée avant de parcourir toutes les annonces.
      </p>

      <div class="flex flex-col gap-3 md:flex-row">
        <input
          :value="question"
          type="text"
          placeholder="Ex: Je veux surtout un bon rapport surface/prix"
          class="h-12 flex-1 rounded-xl border border-slate-300 bg-white px-4 text-slate-900 outline-none transition focus:border-cyan-400 focus:ring-2 focus:ring-cyan-100"
          @input="emit('update:question', ($event.target as HTMLInputElement).value)"
        />
        <button
          type="button"
          :disabled="isLoading || !hasResults"
          class="h-12 rounded-xl bg-cyan-700 px-6 font-semibold text-white transition hover:bg-cyan-600 disabled:cursor-not-allowed disabled:opacity-60"
          @click="emit('ask')"
        >
          {{ isLoading ? "Analyse..." : "Demander un conseil" }}
        </button>
      </div>

      <p
        v-if="error"
        class="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700"
      >
        {{ error }}
      </p>

      <div
        v-if="answer"
        class="space-y-3 rounded-2xl border border-emerald-200 bg-emerald-50/80 px-4 py-4"
      >
        <p class="text-sm font-semibold uppercase tracking-wide text-emerald-800">Recommandation</p>
        <p class="whitespace-pre-line text-sm leading-6 text-emerald-950">{{ answer }}</p>
        <a
          v-if="recommendedUrl"
          :href="recommendedUrl"
          target="_blank"
          rel="noreferrer"
          class="inline-flex text-sm font-semibold text-emerald-700 hover:text-emerald-600"
        >
          Ouvrir l'annonce conseillée ->
        </a>
      </div>
    </div>
  </section>
</template>
