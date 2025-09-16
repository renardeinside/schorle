import type { Config } from "orval";

export default {
  fastapi: {
    input: "./api.json",
    output: {
      client: "react-query",
      httpClient: "fetch",
      override: {
        query: {
          useQuery: true,
          useSuspenseQuery: true,
        },
      },
    },
  },
} satisfies Config;
