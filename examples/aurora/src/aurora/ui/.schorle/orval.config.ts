export default {
  fastapi: {
    output: {
      target: "../app/lib/api.ts",
      client: "react-query",
      httpClient: "fetch",
      prettier: true,
      override: {
        query: {
          useQuery: true,
          useSuspenseQuery: true,
        },
      },
    },
  },
};
