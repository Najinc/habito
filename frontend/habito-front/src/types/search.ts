export type SearchPayload = {
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
  lat?: number | null;
  lng?: number | null;
  first_publication_date?: number | null;
};

export type SearchResult = {
  score: number;
  payload: SearchPayload;
};

export type ChatAdviceResponse = {
  answer: string;
  recommended_url?: string | null;
};
