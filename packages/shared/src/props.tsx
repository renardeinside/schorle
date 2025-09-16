import React, {
  createContext,
  useContext,
  type PropsWithChildren,
} from "react";

const PropsContext = createContext<unknown>(null);

export function PropsProvider({
  value,
  children,
}: PropsWithChildren<{ value: unknown }>) {
  return (
    <PropsContext.Provider value={value}>{children}</PropsContext.Provider>
  );
}

export function useProps<T = unknown>(): T {
  return useContext(PropsContext) as T;
}
