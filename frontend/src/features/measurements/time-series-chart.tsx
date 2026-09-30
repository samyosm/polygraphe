"use client";

import { useEffect, useRef } from "react";
import uPlot from "uplot";
import "uplot/dist/uPlot.min.css";
import { type ChartTheme, readChartTheme } from "./chart-theme";
import type { FieldDisplay } from "./kinds";
import type { Series } from "./store";

const HEIGHT = 180;
/** While live, the chart follows the last LIVE_WINDOW_S seconds. */
const LIVE_WINDOW_S = 120;
const formatTime = uPlot.fmtDate("{HH}:{mm}:{ss}");

interface Props {
  series: Series;
  fields: FieldDisplay[];
  live: boolean;
}

/**
 * uPlot is used imperatively: data goes from the store to the canvas without going
 * through React, at most once per animation frame.
 */
export function TimeSeriesChart({ series, fields, live }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const plotRef = useRef<uPlot>(null);
  const liveRef = useRef(live);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const data = () =>
      [
        series.times,
        ...fields.map((f) => series.column(f.key)),
      ] as uPlot.AlignedData;
    const options = buildOptions(
      container.clientWidth,
      fields,
      readChartTheme(container),
      liveRef,
    );
    const plot = new uPlot(options, data(), container);
    plotRef.current = plot;

    let frame = 0;
    const unsubscribe = series.subscribe(() => {
      frame ||= requestAnimationFrame(() => {
        frame = 0;
        plot.setData(data());
      });
    });
    const resizeObserver = new ResizeObserver(([entry]) =>
      plot.setSize({ width: entry.contentRect.width, height: HEIGHT }),
    );
    resizeObserver.observe(container);

    return () => {
      unsubscribe();
      cancelAnimationFrame(frame);
      resizeObserver.disconnect();
      plot.destroy();
      plotRef.current = null;
    };
  }, [series, fields]);

  // Switching between following the live window and showing everything.
  useEffect(() => {
    liveRef.current = live;
    const plot = plotRef.current;
    if (plot) plot.setData(plot.data);
  }, [live]);

  return (
    <div ref={containerRef} className="w-full" style={{ height: HEIGHT }} />
  );
}

function buildOptions(
  width: number,
  fields: FieldDisplay[],
  theme: ChartTheme,
  liveRef: { current: boolean },
): uPlot.Options {
  const axis: uPlot.Axis = {
    stroke: theme.axis,
    font: theme.font,
    grid: { stroke: theme.grid, width: 1 },
    ticks: { show: false },
  };
  return {
    width,
    height: HEIGHT,
    legend: { show: false },
    cursor: { drag: { x: true, y: false } },
    scales: {
      x: {
        time: true,
        range: (_, min, max) => {
          if (min == null || max == null) {
            const now = Date.now() / 1000;
            return [now - LIVE_WINDOW_S, now];
          }
          return liveRef.current ? [max - LIVE_WINDOW_S, max] : [min, max];
        },
      },
    },
    axes: [
      {
        ...axis,
        values: (_, splits) =>
          splits.map((t) => formatTime(new Date(t * 1000))),
      },
      { ...axis, size: 48 },
    ],
    series: [
      {},
      ...fields.map((field, i) => ({
        label: field.label,
        stroke: theme.palette[i % theme.palette.length],
        width: 1.5,
        points: { show: false, size: 4, filter: isolatedPoints },
      })),
    ],
  };
}

/** A line needs two points: draw points with no neighbour (e.g. after a gap) as dots. */
const isolatedPoints: uPlot.Series.Points.Filter = (plot, seriesIdx) => {
  const values = plot.data[seriesIdx];
  const isolated: number[] = [];
  for (let i = 0; i < values.length; i++) {
    if (values[i] != null && values[i - 1] == null && values[i + 1] == null) {
      isolated.push(i);
    }
  }
  return isolated.length > 0 ? isolated : null;
};
