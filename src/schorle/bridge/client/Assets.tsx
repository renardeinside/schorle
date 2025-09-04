export function Assets({ cssPath }: { cssPath: string | null }) {
  return <>{cssPath ? <link rel="stylesheet" href={cssPath} /> : null}</>;
}
