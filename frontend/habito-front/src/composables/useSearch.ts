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

export const cityCoordinates: Record<string, { lat: number; lng: number }> = {
  Amiens: { lat: 49.8941, lng: 2.2958 },
  Angers: { lat: 47.4829, lng: -0.5515 },
  Bordeaux: { lat: 44.8378, lng: -0.5792 },
  Caen: { lat: 49.1829, lng: -0.355 },
  Cannes: { lat: 43.5524, lng: 7.0176 },
  Dijon: { lat: 47.322, lng: 5.04 },
  Grenoble: { lat: 45.1885, lng: 5.7245 },
  Lille: { lat: 50.6292, lng: 3.0573 },
  Lyon: { lat: 45.764, lng: 4.8357 },
  Marseille: { lat: 43.2965, lng: 5.3698 },
  Montpellier: { lat: 43.6108, lng: 3.8767 },
  Nantes: { lat: 47.2184, lng: -1.5536 },
  Nice: { lat: 43.7102, lng: 7.262 },
  Paris: { lat: 48.8566, lng: 2.3522 },
  Reims: { lat: 49.2583, lng: 4.0317 },
  Rennes: { lat: 48.1173, lng: -1.6778 },
  Strasbourg: { lat: 48.5734, lng: 7.7521 },
  Toulouse: { lat: 43.6047, lng: 1.4442 },
  Tours: { lat: 47.3941, lng: 0.6848 },
};

export function useSearch() {
  const query = ref("appartement");
  const searchCity = ref("Lille");
  const filterRadius = ref("10");
  const sortBy = ref<"score" | "price-asc" | "price-desc" | "square-asc" | "square-desc" | "newest">("score");

  const isLoading = ref(false);
  const errorMessage = ref("");
  const successMessage = ref("");

  const allResults = ref<SearchResult[]>([]);
  const results = ref<SearchResult[]>([]);
  const displayedResultsCount = ref(10); // Nombre de résultats affichés
  const resultsPerPage = 10; // Nombre à ajouter au scroll

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

  const paginatedResults = computed(() => {
    return results.value.slice(0, displayedResultsCount.value);
  });

  const hasMoreResults = computed(() => {
    return displayedResultsCount.value < results.value.length;
  });

  const loadMoreResults = () => {
    displayedResultsCount.value = Math.min(
      displayedResultsCount.value + resultsPerPage,
      results.value.length
    );
  };

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

  const sortResults = () => {
    const sorted = [...results.value];

    switch (sortBy.value) {
      case "price-asc":
        sorted.sort((a, b) => (a.payload.price || 0) - (b.payload.price || 0));
        break;
      case "price-desc":
        sorted.sort((a, b) => (b.payload.price || 0) - (a.payload.price || 0));
        break;
      case "square-asc":
        sorted.sort((a, b) => (a.payload.square || 0) - (b.payload.square || 0));
        break;
      case "square-desc":
        sorted.sort((a, b) => (b.payload.square || 0) - (a.payload.square || 0));
        break;
      case "newest":
        sorted.sort((a, b) => (b.payload.first_publication_date || 0) - (a.payload.first_publication_date || 0));
        break;
      case "score":
      default:
        sorted.sort((a, b) => b.score - a.score);
    }

    results.value = sorted;
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
    sortResults(); // Apply sorting after filtering
    displayedResultsCount.value = resultsPerPage; // Reset pagination
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
      displayedResultsCount.value = resultsPerPage;
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
    cityCoordinates,
    query,
    searchCity,
    filterRadius,
    sortBy,
    isLoading,
    errorMessage,
    successMessage,
    allResults,
    results,
    paginatedResults,
    displayedResultsCount,
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
  };
}
