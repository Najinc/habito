import { computed, ref } from "vue";
import type { ChatAdviceResponse, SearchResult } from "../types/search";

export const cityOptions = [
  "Amiens",
  "Angers",
  "Bordeaux",
  "Caen",
  "Cannes",
  "Dijon",
  "Grenoble",
  "Lille",
  "Lyon",
  "Marseille",
  "Montpellier",
  "Nantes",
  "Nice",
  "Paris",
  "Reims",
  "Rennes",
  "Strasbourg",
  "Toulouse",
  "Tours",
];

export function useSearch() {
  const query = ref("appartement");
  const searchCity = ref("Lille");

  const isLoading = ref(false);
  const errorMessage = ref("");
  const successMessage = ref("");

  const allResults = ref<SearchResult[]>([]);
  const results = ref<SearchResult[]>([]);

  const filters = ref({
    minPrice: "",
    maxPrice: "",
    minSquare: "",
    maxSquare: "",
    minRooms: "",
    minScore: "",
  });

  const chatQuestion = ref("Quel est le meilleur bien pour moi et pourquoi ?");
  const chatAnswer = ref("");
  const chatRecommendedUrl = ref("");
  const chatError = ref("");
  const isChatLoading = ref(false);

  const hasResults = computed(() => results.value.length > 0);

  const formatPrice = (value?: number | null): string => {
    if (typeof value !== "number") return "Prix non renseigne";
    return new Intl.NumberFormat("fr-FR", {
      style: "currency",
      currency: "EUR",
      maximumFractionDigits: 0,
    }).format(value);
  };

  const shortText = (text?: string | null): string => {
    if (!text) return "Description non disponible.";
    return text.length > 240 ? `${text.slice(0, 240)}...` : text;
  };

  const scoreStyle = (score: number): Record<string, string> => {
    const clamped = Math.max(0, Math.min(4, score));
    const normalized = clamped / 4;
    const hue = Math.round(normalized * 120);
    const startHue = Math.max(0, hue - 16);
    const endHue = Math.min(130, hue + 8);

    return {
      backgroundImage: `linear-gradient(135deg, hsl(${startHue} 85% 92%), hsl(${endHue} 70% 80%))`,
      color: "#0f172a",
      borderColor: `hsl(${endHue} 45% 62%)`,
    };
  };

  const applyFilters = () => {
    results.value = allResults.value.filter((item) => {
      const price = item.payload.price;
      const square = item.payload.square;
      const rooms = item.payload.rooms;
      const score = item.score;

      if (filters.value.minPrice && price && price < parseFloat(filters.value.minPrice)) return false;
      if (filters.value.maxPrice && price && price > parseFloat(filters.value.maxPrice)) return false;
      if (filters.value.minSquare && square && square < parseFloat(filters.value.minSquare)) return false;
      if (filters.value.maxSquare && square && square > parseFloat(filters.value.maxSquare)) return false;
      if (filters.value.minRooms && rooms && rooms < parseFloat(filters.value.minRooms)) return false;
      if (filters.value.minScore && score < parseFloat(filters.value.minScore)) return false;

      return true;
    });
  };

  const search = async () => {
    const cleanQuery = query.value.trim();
    const city = searchCity.value.trim();

    if (!cleanQuery || !city) {
      errorMessage.value = "Saisir une recherche et une ville.";
      return;
    }

    isLoading.value = true;
    errorMessage.value = "";
    successMessage.value = "";

    try {
      const searchResponse = await fetch("http://localhost:8000/api/search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: cleanQuery, city }),
      });

      if (!searchResponse.ok) {
        const body = await searchResponse.text();
        throw new Error(body || `Erreur HTTP ${searchResponse.status}`);
      }

      const data = (await searchResponse.json()) as SearchResult[];
      allResults.value = Array.isArray(data) ? data : [];
      applyFilters();

      chatAnswer.value = "";
      chatRecommendedUrl.value = "";
      chatError.value = "";

      if (allResults.value.length === 0) {
        successMessage.value = `Aucune annonce trouvee a ${city}. Le scraping en temps reel est en cours.`;
      } else {
        successMessage.value = `${allResults.value.length} annonce(s) trouvee(s) a ${city}.`;
      }
    } catch (error) {
      allResults.value = [];
      results.value = [];
      errorMessage.value = error instanceof Error ? error.message : "Erreur inconnue.";
      successMessage.value = "";
    } finally {
      isLoading.value = false;
    }
  };

  const askAdvisor = async () => {
    if (results.value.length === 0) {
      chatError.value = "Lance d'abord une recherche avec des resultats.";
      return;
    }

    isChatLoading.value = true;
    chatError.value = "";

    try {
      const payloadResults = results.value.slice(0, 10).map((item) => ({
        score: item.score,
        payload: {
          subject: item.payload.subject,
          body: item.payload.body,
          price: item.payload.price,
          city: item.payload.city,
          square: item.payload.square,
          rooms: item.payload.rooms,
          url: item.payload.url,
        },
      }));

      const response = await fetch("http://localhost:8000/api/chat/advice", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: query.value.trim(),
          city: searchCity.value.trim(),
          question: chatQuestion.value.trim(),
          results: payloadResults,
        }),
      });

      if (!response.ok) {
        const body = await response.text();
        throw new Error(body || `Erreur HTTP ${response.status}`);
      }

      const data = (await response.json()) as ChatAdviceResponse;
      chatAnswer.value = data.answer || "Pas de conseil disponible pour le moment.";
      chatRecommendedUrl.value = data.recommended_url || "";
    } catch (error) {
      chatAnswer.value = "";
      chatRecommendedUrl.value = "";
      chatError.value = error instanceof Error ? error.message : "Erreur chatbot inconnue.";
    } finally {
      isChatLoading.value = false;
    }
  };

  return {
    cityOptions,
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
  };
}
