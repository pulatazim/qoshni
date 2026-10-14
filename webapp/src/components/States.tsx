// Ekran holatlari: yuklanmoqda / xato / bo'sh — bitta markazlashgan blok.

import type { ReactNode } from "react";

export function Notice({
  title,
  text,
  action,
  children,
}: {
  title?: string;
  text?: string;
  action?: { label: string; onClick: () => void };
  children?: ReactNode;
}) {
  return (
    <div className="notice">
      {title && <h2 className="notice-title">{title}</h2>}
      {text && <p className="notice-text">{text}</p>}
      {action && (
        <button type="button" className="btn btn-ghost" onClick={action.onClick}>
          {action.label}
        </button>
      )}
      {children}
    </div>
  );
}
