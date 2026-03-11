export interface User {
  id: number;
  email: string | null;
  name: string | null;
  provider: string;
  created_at: string;
}
