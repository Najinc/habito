export type SearchPayload = {
  subject?: string | null;
  body?: string | null;
  price?: number | null;
  city?: string | null;
  square?: number | null;
  rooms?: number | null;
  url?: string | null;
  images?: string[] | null;
  lat?: number | null;
  lng?: number | null;
  first_publication_date?: number | null;
  owner_type?: string | null;
  seniority?: string | null;
  nb_views?: number | null;
  has_phone?: boolean | null;
  score_breakdown?: {
    vector_score: number;
    rerank_score?: number;
    city_boost: number;
    date_boost: number;
    image_boost: number;
    verified_boost: number;
    total_score: number;
  } | null;
};

export type SearchResult = {
  score: number;
  payload: SearchPayload;
};

export type ChatAdviceResponse = {
  answer: string;
  recommended_url?: string | null;
};
