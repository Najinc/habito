<script setup lang="ts">
import { computed } from "vue";
import type { SearchResult } from "../types/search";

interface Props {
  selectedResults: SearchResult[];
  formatPrice: (value?: number | null) => string;
}

const props = defineProps<Props>();
const emit = defineEmits<{
  close: [];
  exportCSV: [];
  exportPDF: [];
}>();

const hasSelected = computed(() => props.selectedResults.length > 0);

const exportToCSV = () => {
  if (!hasSelected.value) return;

  // Prepare CSV headers
  const headers = [
    "Critère",
    ...props.selectedResults.map((_, i) => `Annonce ${i + 1}`),
  ];
  const rows = [headers];

  // Prepare data rows
  const criteria = [
    { label: "Titre", key: (r: SearchResult) => r.payload.subject },
    {
      label: "Prix",
      key: (r: SearchResult) => props.formatPrice(r.payload.price),
    },
    {
      label: "Surface (m²)",
      key: (r: SearchResult) => r.payload.square || "-",
    },
    { label: "Pièces", key: (r: SearchResult) => r.payload.rooms || "-" },
    { label: "Ville", key: (r: SearchResult) => r.payload.city || "-" },
    { label: "Vues", key: (r: SearchResult) => r.payload.nb_views || "-" },
    {
      label: "Type",
      key: (r: SearchResult) => r.payload.owner_type || "Particulier",
    },
    {
      label: "Photos",
      key: (r: SearchResult) => (r.payload.images?.length || 0) + "",
    },
    { label: "Score", key: (r: SearchResult) => r.score.toFixed(2) },
  ];

  for (const criterion of criteria) {
    const row = [
      criterion.label,
      ...props.selectedResults.map((r) => criterion.key(r)),
    ];
    rows.push(row);
  }

  // Convert to CSV string
  const csv = rows
    .map((row) => row.map((cell) => `"${cell}"`).join(","))
    .join("\n");

  // Download
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
  const link = document.createElement("a");
  const url = URL.createObjectURL(blob);
  link.setAttribute("href", url);
  link.setAttribute(
    "download",
    `comparaison_annonces_${new Date().toISOString().split("T")[0]}.csv`,
  );
  link.style.visibility = "hidden";
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
};

const generatePDF = () => {
  if (!hasSelected.value) return;

  // Simple PDF generation with basic HTML approach
  const htmlContent = `
    <html>
      <head>
        <meta charset="utf-8">
        <title>Comparaison d'annonces</title>
        <style>
          body { font-family: Arial, sans-serif; margin: 20px; }
          h1 { text-align: center; color: #1e293b; }
          h2 { color: #475569; margin-top: 20px; }
          table { width: 100%; border-collapse: collapse; margin-bottom: 20px; }
          th, td { border: 1px solid #cbd5e1; padding: 12px; text-align: left; }
          th { background-color: #f1f5f9; font-weight: bold; }
          tr:nth-child(even) { background-color: #f8fafc; }
          .listing { page-break-inside: avoid; margin: 20px 0; padding: 15px; background: #f1f5f9; border-radius: 8px; }
          .listing h3 { margin: 0 0 10px 0; color: #1e293b; }
          .listing p { margin: 5px 0; color: #475569; }
          .price { font-size: 18px; font-weight: bold; color: #059669; }
        </style>
      </head>
      <body>
        <h1>Comparaison d'annonces immobilières</h1>
        
        <h2>Tableau Comparatif</h2>
        <table>
          <thead>
            <tr>
              <th>Critère</th>
              ${props.selectedResults.map((_, i) => `<th>Annonce ${i + 1}</th>`).join("")}
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><strong>Titre</strong></td>
              ${props.selectedResults.map((r) => `<td>${r.payload.subject}</td>`).join("")}
            </tr>
            <tr>
              <td><strong>Prix</strong></td>
              ${props.selectedResults.map((r) => `<td class="price">${props.formatPrice(r.payload.price)}</td>`).join("")}
            </tr>
            <tr>
              <td><strong>Surface (m²)</strong></td>
              ${props.selectedResults.map((r) => `<td>${r.payload.square || "-"}</td>`).join("")}
            </tr>
            <tr>
              <td><strong>Pièces</strong></td>
              ${props.selectedResults.map((r) => `<td>${r.payload.rooms || "-"}</td>`).join("")}
            </tr>
            <tr>
              <td><strong>Type</strong></td>
              ${props.selectedResults.map((r) => `<td>${r.payload.owner_type || "Particulier"}</td>`).join("")}
            </tr>
            <tr>
              <td><strong>Vues</strong></td>
              ${props.selectedResults.map((r) => `<td>${r.payload.nb_views || "-"}</td>`).join("")}
            </tr>
            <tr>
              <td><strong>Photos</strong></td>
              ${props.selectedResults.map((r) => `<td>${r.payload.images?.length || 0}</td>`).join("")}
            </tr>
            <tr>
              <td><strong>Score</strong></td>
              ${props.selectedResults.map((r) => `<td>${r.score.toFixed(2)}</td>`).join("")}
            </tr>
          </tbody>
        </table>

        <h2>Détails des annonces</h2>
        ${props.selectedResults
          .map(
            (r) => `
          <div class="listing">
            <h3>${r.payload.subject}</h3>
            <p><strong>Localisation:</strong> ${r.payload.city}</p>
            <p class="price">${props.formatPrice(r.payload.price)}</p>
            <p><strong>Surface:</strong> ${r.payload.square || "-"} m²</p>
            <p><strong>Pièces:</strong> ${r.payload.rooms || "-"}</p>
            <p><strong>Type:</strong> ${r.payload.owner_type || "Particulier"}</p>
            <p><strong>Vues:</strong> ${r.payload.nb_views || "-"}</p>
            <p><strong>Score:</strong> ${r.score.toFixed(2)}</p>
            <p><strong>Lien:</strong> <a href="${r.payload.url}" target="_blank">${r.payload.url}</a></p>
          </div>
        `,
          )
          .join("")}
      </body>
    </html>
  `;

  // Open in new window for printing
  const printWindow = window.open("", "_blank");
  if (printWindow) {
    printWindow.document.write(htmlContent);
    printWindow.document.close();
    setTimeout(() => {
      printWindow.print();
    }, 250);
  }
};
</script>

<template>
  <teleport to="body">
    <div
      class="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 p-4"
    >
      <!-- Modal content -->
      <div
        @click.stop
        class="max-h-[90vh] w-full max-w-4xl overflow-y-auto rounded-2xl bg-white shadow-2xl"
      >
        <!-- Inner wrapper -->
        <div class="space-y-6 p-6 md:p-10">
          <!-- Header -->
          <div class="flex items-center justify-between gap-4">
            <div>
              <h2 class="text-2xl font-bold text-slate-900">
                Comparateur d'annonces
              </h2>
              <p class="mt-1 text-sm text-slate-600">
                {{ selectedResults.length }} annonce(s) sélectionnée(s)
              </p>
            </div>
            <button
              @click="$emit('close')"
              class="rounded-lg text-slate-400 transition hover:bg-slate-200 hover:text-slate-600"
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

          <!-- Export buttons -->
          <div v-if="hasSelected" class="flex flex-wrap gap-2">
            <button
              @click="exportToCSV"
              class="inline-flex items-center gap-2 rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-emerald-700"
            >
              <svg
                class="h-4 w-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                />
              </svg>
              Télécharger CSV
            </button>
            <button
              @click="generatePDF"
              class="inline-flex items-center gap-2 rounded-lg bg-red-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-red-700"
            >
              <svg
                class="h-4 w-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"
                />
              </svg>
              Imprimer/PDF
            </button>
          </div>

          <!-- Comparison table -->
          <div
            v-if="hasSelected"
            class="overflow-x-auto rounded-lg border border-slate-200"
          >
            <table class="w-full">
              <thead class="bg-slate-100">
                <tr>
                  <th
                    class="border-b border-slate-200 px-4 py-3 text-left text-sm font-semibold text-slate-900"
                  >
                    Critère
                  </th>
                  <th
                    v-for="(result, idx) in selectedResults"
                    :key="idx"
                    class="border-b border-l border-slate-200 px-4 py-3 text-left text-sm font-semibold text-slate-900"
                  >
                    Annonce {{ idx + 1 }}
                  </th>
                </tr>
              </thead>
              <tbody>
                <tr class="border-b border-slate-200">
                  <td
                    class="bg-slate-50 px-4 py-3 text-sm font-medium text-slate-700"
                  >
                    Titre
                  </td>
                  <td
                    v-for="(result, idx) in selectedResults"
                    :key="idx"
                    class="border-l border-slate-200 px-4 py-3 text-sm text-slate-900"
                  >
                    {{ result.payload.subject }}
                  </td>
                </tr>

                <tr class="border-b border-slate-200">
                  <td
                    class="bg-slate-50 px-4 py-3 text-sm font-medium text-slate-700"
                  >
                    Prix
                  </td>
                  <td
                    v-for="(result, idx) in selectedResults"
                    :key="idx"
                    class="border-l border-slate-200 px-4 py-3 text-sm font-bold text-emerald-600"
                  >
                    {{ formatPrice(result.payload.price) }}
                  </td>
                </tr>

                <tr class="border-b border-slate-200">
                  <td
                    class="bg-slate-50 px-4 py-3 text-sm font-medium text-slate-700"
                  >
                    Surface (m²)
                  </td>
                  <td
                    v-for="(result, idx) in selectedResults"
                    :key="idx"
                    class="border-l border-slate-200 px-4 py-3 text-sm text-slate-900"
                  >
                    {{ result.payload.square || "-" }}
                  </td>
                </tr>

                <tr class="border-b border-slate-200">
                  <td
                    class="bg-slate-50 px-4 py-3 text-sm font-medium text-slate-700"
                  >
                    Pièces
                  </td>
                  <td
                    v-for="(result, idx) in selectedResults"
                    :key="idx"
                    class="border-l border-slate-200 px-4 py-3 text-sm text-slate-900"
                  >
                    {{ result.payload.rooms || "-" }}
                  </td>
                </tr>

                <tr class="border-b border-slate-200">
                  <td
                    class="bg-slate-50 px-4 py-3 text-sm font-medium text-slate-700"
                  >
                    Localisation
                  </td>
                  <td
                    v-for="(result, idx) in selectedResults"
                    :key="idx"
                    class="border-l border-slate-200 px-4 py-3 text-sm text-slate-900"
                  >
                    {{ result.payload.city }}
                  </td>
                </tr>

                <tr class="border-b border-slate-200">
                  <td
                    class="bg-slate-50 px-4 py-3 text-sm font-medium text-slate-700"
                  >
                    Type
                  </td>
                  <td
                    v-for="(result, idx) in selectedResults"
                    :key="idx"
                    class="border-l border-slate-200 px-4 py-3 text-sm text-slate-900"
                  >
                    <span
                      :class="{
                        'rounded-full px-2 py-1 text-xs font-medium': true,
                        'bg-blue-100 text-blue-800':
                          result.payload.owner_type === 'Agence',
                        'bg-emerald-100 text-emerald-800':
                          result.payload.owner_type !== 'Agence',
                      }"
                    >
                      {{ result.payload.owner_type || "Particulier" }}
                    </span>
                  </td>
                </tr>

                <tr class="border-b border-slate-200">
                  <td
                    class="bg-slate-50 px-4 py-3 text-sm font-medium text-slate-700"
                  >
                    Vues
                  </td>
                  <td
                    v-for="(result, idx) in selectedResults"
                    :key="idx"
                    class="border-l border-slate-200 px-4 py-3 text-sm text-slate-900"
                  >
                    {{ result.payload.nb_views || "-" }}
                  </td>
                </tr>

                <tr class="border-b border-slate-200">
                  <td
                    class="bg-slate-50 px-4 py-3 text-sm font-medium text-slate-700"
                  >
                    Photos
                  </td>
                  <td
                    v-for="(result, idx) in selectedResults"
                    :key="idx"
                    class="border-l border-slate-200 px-4 py-3 text-sm text-slate-900"
                  >
                    {{ result.payload.images?.length || 0 }}
                  </td>
                </tr>

                <tr class="border-b border-slate-200">
                  <td
                    class="bg-slate-50 px-4 py-3 text-sm font-medium text-slate-700"
                  >
                    Score
                  </td>
                  <td
                    v-for="(result, idx) in selectedResults"
                    :key="idx"
                    class="border-l border-slate-200 px-4 py-3 text-sm font-bold text-indigo-600"
                  >
                    {{ result.score.toFixed(2) }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- Empty state -->
          <div
            v-else
            class="rounded-lg border border-dashed border-slate-300 bg-slate-50 p-8 text-center"
          >
            <svg
              class="mx-auto h-12 w-12 text-slate-400"
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
            <p class="mt-2 text-sm text-slate-600">
              Sélectionnez 2-3 annonces pour les comparer
            </p>
          </div>
        </div>
      </div>
    </div>
  </teleport>
</template>
