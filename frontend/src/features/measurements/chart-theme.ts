/** Reads the design tokens from globals.css, since canvas cannot use CSS variables. */
export function readChartTheme(element: HTMLElement) {
  const root = getComputedStyle(document.documentElement);
  const token = (name: string) =>
    root.getPropertyValue(`--color-${name}`).trim();
  return {
    palette: [1, 2, 3, 4, 5, 6].map((i) => token(`chart-${i}`)),
    grid: token("chart-grid"),
    axis: token("chart-axis"),
    font: `12px ${getComputedStyle(element).fontFamily}`,
  };
}

export type ChartTheme = ReturnType<typeof readChartTheme>;
