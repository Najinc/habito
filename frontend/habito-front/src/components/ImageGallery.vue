<script setup lang="ts">
import { ref, computed } from "vue";

interface Props {
  images?: string[] | null;
  title?: string;
  inDetailView?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  images: null,
  title: "Images",
  inDetailView: false,
});

const currentIndex = ref(0);
const isFullscreen = ref(false);

const hasImages = computed(() => props.images && props.images.length > 0);
const currentImage = computed(() => {
  if (!hasImages.value) return null;
  return props.images![currentIndex.value];
});

const totalImages = computed(() => props.images?.length ?? 0);

const goToPrevious = () => {
  if (!hasImages.value) return;
  currentIndex.value =
    (currentIndex.value - 1 + props.images!.length) % props.images!.length;
};

const goToNext = () => {
  if (!hasImages.value) return;
  currentIndex.value = (currentIndex.value + 1) % props.images!.length;
};

const goToImage = (index: number) => {
  if (index >= 0 && index < totalImages.value) {
    currentIndex.value = index;
  }
};

const toggleFullscreen = () => {
  isFullscreen.value = !isFullscreen.value;
};

const closeFullscreen = () => {
  isFullscreen.value = false;
};

// Keyboard navigation
const handleKeydown = (e: KeyboardEvent) => {
  if (!isFullscreen.value) return;
  if (e.key === "ArrowLeft") goToPrevious();
  if (e.key === "ArrowRight") goToNext();
  if (e.key === "Escape") closeFullscreen();
};
</script>

<template>
  <!-- No images fallback -->
  <div
    v-if="!hasImages"
    class="rounded-lg bg-slate-100 p-4 text-center text-sm text-slate-500"
  >
    Aucune image disponible
  </div>

  <!-- Main gallery view -->
  <div v-else class="space-y-3">
    <!-- Main image with controls -->
    <div class="relative overflow-hidden rounded-lg bg-slate-900">
      <!-- Image -->
      <img
        :src="currentImage"
        :alt="title"
        :class="inDetailView ? 'h-80' : 'h-40'"
        class="w-full cursor-pointer object-cover transition hover:opacity-95"
        @click="toggleFullscreen"
      />

      <!-- Image counter -->
      <div
        class="absolute right-3 top-3 rounded-lg bg-slate-950/70 px-3 py-1 text-xs font-medium text-white backdrop-blur"
      >
        {{ currentIndex + 1 }} / {{ totalImages }}
      </div>

      <!-- Previous button -->
      <button
        v-if="totalImages > 1"
        @click="goToPrevious"
        class="absolute left-3 top-1/2 -translate-y-1/2 rounded-lg bg-white/80 p-2 text-slate-900 transition hover:bg-white active:scale-95"
        aria-label="Image précédente"
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
            d="M15 19l-7-7 7-7"
          />
        </svg>
      </button>

      <!-- Next button -->
      <button
        v-if="totalImages > 1"
        @click="goToNext"
        class="absolute right-3 top-1/2 -translate-y-1/2 rounded-lg bg-white/80 p-2 text-slate-900 transition hover:bg-white active:scale-95"
        aria-label="Image suivante"
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
            d="M9 5l7 7-7 7"
          />
        </svg>
      </button>

      <!-- Fullscreen button -->
      <button
        @click="toggleFullscreen"
        class="absolute bottom-3 right-3 rounded-lg bg-slate-950/70 p-2 text-white transition hover:bg-slate-950 backdrop-blur"
        aria-label="Fullscreen"
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
            d="M10 6H6v4m12-4h4v4M6 18h-4v-4m16 4h4v-4"
          />
        </svg>
      </button>
    </div>

    <!-- Thumbnail strip -->
    <div v-if="totalImages > 1" class="flex gap-2 overflow-x-auto">
      <button
        v-for="(image, index) in images"
        :key="index"
        @click="goToImage(index)"
        :class="{
          'ring-2 ring-indigo-500': currentIndex === index,
        }"
        class="relative h-16 w-16 flex-shrink-0 overflow-hidden rounded-md border border-slate-200 transition hover:border-indigo-400"
      >
        <img
          :src="image"
          :alt="`Thumbnail ${index + 1}`"
          class="h-full w-full object-cover"
        />
      </button>
    </div>
  </div>

  <!-- Fullscreen modal -->
  <teleport to="body">
    <div
      v-if="isFullscreen"
      @keydown="handleKeydown"
      tabindex="0"
      class="fixed inset-0 z-50 flex items-center justify-center bg-slate-950"
    >
      <!-- Close button -->
      <button
        @click="closeFullscreen"
        class="absolute right-6 top-6 rounded-lg bg-white/10 p-2 text-white transition hover:bg-white/20 backdrop-blur"
        aria-label="Fermer"
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

      <!-- Image counter -->
      <div
        class="absolute bottom-6 left-6 rounded-lg bg-white/10 px-4 py-2 text-sm font-medium text-white backdrop-blur"
      >
        {{ currentIndex + 1 }} / {{ totalImages }}
      </div>

      <!-- Previous button -->
      <button
        v-if="totalImages > 1"
        @click="goToPrevious"
        class="absolute left-6 top-1/2 -translate-y-1/2 rounded-lg bg-white/10 p-3 text-white transition hover:bg-white/20 active:scale-95 backdrop-blur"
        aria-label="Image précédente"
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
            d="M15 19l-7-7 7-7"
          />
        </svg>
      </button>

      <!-- Main fullscreen image -->
      <img
        :src="currentImage"
        :alt="title"
        class="max-h-full max-w-full object-contain"
      />

      <!-- Next button -->
      <button
        v-if="totalImages > 1"
        @click="goToNext"
        class="absolute right-6 top-1/2 -translate-y-1/2 rounded-lg bg-white/10 p-3 text-white transition hover:bg-white/20 active:scale-95 backdrop-blur"
        aria-label="Image suivante"
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
            d="M9 5l7 7-7 7"
          />
        </svg>
      </button>
    </div>
  </teleport>
</template>
