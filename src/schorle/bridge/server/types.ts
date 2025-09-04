export type BuildProps = {
  projectRoot: string;
  appRoot: string;
  pagesRoot: string;
  schorleRoot: string;
};

export type RenderProps = BuildProps & {
  pageName: string;
};

export type Manifest = { js: string; css?: string };
