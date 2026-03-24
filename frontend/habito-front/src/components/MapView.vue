<script setup lang="ts">
import { ref, onMounted, watch, computed } from "vue";
import * as L from "leaflet";
import type { SearchResult } from "../types/search";

interface Props {
  results: SearchResult[];
  searchCity: string;
  cityLat: number;
  cityLng: number;
  filterRadius: string;
}

const props = defineProps<Props>();

const emit = defineEmits<{
  updateRadius: [radius: number];
}>();

const mapContainer = ref<HTMLDivElement | null>(null);
let map: L.Map | null = null;
let markersGroup: L.FeatureGroup | null = null;
let radiusCircle: L.Circle | null = null;

const currentRadius = ref(parseFloat(props.filterRadius) || 10);
const filteredResults = computed(() => {
  if (currentRadius.value <= 0) return props.results;

  return props.results.filter((result) => {
    if (!result.payload.lat || !result.payload.lng) return true;
    const distance = calculateDistance(
      props.cityLat,
      props.cityLng,
      result.payload.lat,
      result.payload.lng,
    );
    return distance <= currentRadius.value;
  });
});

const calculateDistance = (
  lat1: number,
  lng1: number,
  lat2: number,
  lng2: number,
): number => {
  const R = 6371; // Earth radius in km
  const dLat = ((lat2 - lat1) * Math.PI) / 180;
  const dLng = ((lng2 - lng1) * Math.PI) / 180;
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos((lat1 * Math.PI) / 180) *
      Math.cos((lat2 * Math.PI) / 180) *
      Math.sin(dLng / 2) *
      Math.sin(dLng / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
};

const initMap = () => {
  if (!mapContainer.value) return;

  // Destroy existing map if it exists
  if (map) {
    map.off();
    map.remove();
  }

  map = L.map(mapContainer.value).setView([props.cityLat, props.cityLng], 12);

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "© OpenStreetMap contributors",
    maxZoom: 19,
  }).addTo(map);

  // Add radius circle
  radiusCircle = L.circle([props.cityLat, props.cityLng], {
    color: "blue",
    fillColor: "#3b82f6",
    fillOpacity: 0.1,
    radius: currentRadius.value * 1000, // Convert km to meters
    weight: 2,
  }).addTo(map);

  // Add city center marker
  L.circleMarker([props.cityLat, props.cityLng], {
    radius: 8,
    fillColor: "#0284c7",
    color: "#fff",
    weight: 2,
    opacity: 1,
    fillOpacity: 0.8,
  })
    .bindPopup(`<strong>${props.searchCity}</strong><br/>Centre-ville`)
    .addTo(map);

  // Create markers group
  markersGroup = L.featureGroup().addTo(map);

  // Add markers for results
  updateMarkers();
};

const updateMarkers = () => {
  if (!map || !markersGroup) return;

  markersGroup.clearLayers();

  filteredResults.value.forEach((result) => {
    if (!result.payload.lat || !result.payload.lng) return;

    const distance = calculateDistance(
      props.cityLat,
      props.cityLng,
      result.payload.lat,
      result.payload.lng,
    );
    const price = result.payload.price
      ? `€${result.payload.price.toLocaleString("fr-FR")}`
      : "N/A";

    const color =
      result.score >= 2 ? "#10b981" : result.score >= 1 ? "#f59e0b" : "#ef4444";

    const marker = L.circleMarker([result.payload.lat, result.payload.lng], {
      radius: 8,
      fillColor: color,
      color: "#fff",
      weight: 2,
      opacity: 1,
      fillOpacity: 0.7,
    });

    const popupContent = `
      <div class="text-sm max-w-xs">
        <strong class="text-base block mb-2">${result.payload.subject || "Annonce"}</strong>
        <p class="text-xs text-gray-600 mb-1">${distance.toFixed(1)} km du centre</p>
        <p class="font-semibold text-sm text-blue-600 mb-1">${price}</p>
        <p class="text-xs text-gray-600 mb-2">${result.payload.square ? `${result.payload.square} m²` : ""} ${result.payload.rooms ? `• ${result.payload.rooms} pièces` : ""}</p>
        <a href="${result.payload.url}" target="_blank" rel="noopener" class="text-xs text-sky-600 hover:underline">Voir annonce →</a>
      </div>
    `;

    marker.bindPopup(popupContent);
    markersGroup!.addLayer(marker);
  });

  // Fit map bounds to markers
  if (markersGroup.getLayers().length > 0) {
    map.fitBounds(markersGroup.getBounds().pad(0.1));
  }
};

const updateRadius = () => {
  emit("updateRadius", currentRadius.value);
  if (map && radiusCircle) {
    radiusCircle.setRadius(currentRadius.value * 1000);
  }
  updateMarkers();
};

onMounted(() => {
  initMap();
});

watch([() => props.results, () => props.cityLat, () => props.cityLng], () => {
  if (map) {
    updateMarkers();
  }
});

watch(
  () => props.searchCity,
  () => {
    initMap();
  },
);
</script>

<template>
  <div class="space-y-4">
    <!-- Map Container -->
    <div
      ref="mapContainer"
      class="h-96 w-full rounded-xl border border-slate-200 shadow-sm overflow-hidden"
    ></div>

    <!-- Radius Filter -->
    <div class="space-y-2 rounded-lg bg-slate-50 p-4">
      <label class="text-sm font-semibold text-slate-700"
        >Rayon de recherche: {{ currentRadius }} km</label
      >
      <input
        v-model.number="currentRadius"
        type="range"
        min="1"
        max="100"
        step="1"
        class="w-full cursor-pointer"
        @change="updateRadius"
      />
      <p class="text-xs text-slate-500">
        {{ filteredResults.length }} annonce(s) dans ce rayon
      </p>
    </div>

    <!-- Map Legend -->
    <div class="grid grid-cols-3 gap-2 rounded-lg bg-slate-50 p-3 text-xs">
      <div class="flex items-center gap-2">
        <div class="h-3 w-3 rounded-full bg-green-500"></div>
        <span>Score ≥ 2.0</span>
      </div>
      <div class="flex items-center gap-2">
        <div class="h-3 w-3 rounded-full bg-amber-500"></div>
        <span>Score 1.0-2.0</span>
      </div>
      <div class="flex items-center gap-2">
        <div class="h-3 w-3 rounded-full bg-red-500"></div>
        <span>Score &lt; 1.0</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
:global(.leaflet-container) {
  font-family: inherit;
  font-size: 0.875rem;
}

:global(.leaflet-popup-content) {
  margin: 0;
  padding: 0;
}
</style>
