// Yangi e'lon: forma → POST /listings → bitta rasm yuklash → tafsilot ekraniga o'tish.

import { useEffect, useState } from "react";
import { useAddImage, useCategories, useCreateListing } from "../api/hooks";
import type { Condition, Coordinates, PriceType } from "../api/types";
import { Chip, ChipRow } from "../components/Chip";
import { Notice } from "../components/States";
import { useLang } from "../lib/i18n";
import { askPosition } from "../lib/geo";
import { hasMainButton, mainButton, tap } from "../lib/telegram";

export function Create({ onDone, onBack }: { onDone: (id: number) => void; onBack: () => void }) {
  const { t, lang } = useLang();
  const categories = useCategories();
  const create = useCreateListing();
  const addImage = useAddImage();

  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [price, setPrice] = useState("");
  const [priceType, setPriceType] = useState<PriceType>("fixed");
  const [condition, setCondition] = useState<Condition>("used");
  const [categoryId, setCategoryId] = useState<number | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [gps, setGps] = useState<Coordinates | null>(null);
  const [error, setError] = useState<string | null>(null);

  const busy = create.isPending || addImage.isPending;
  const list = categories.data ?? [];

  function pickFile(next: File | null) {
    setFile(next);
    setError(null);
  }

  async function submit() {
    setError(null);
    if (title.trim().length < 3) {
      setError(t("titleTooShort"));
      return;
    }
    if (categoryId === null) {
      setError(t("categoryRequired"));
      return;
    }
    const parsed = Number(price.replace(/[^\d]/g, ""));
    try {
      const listing = await create.mutateAsync({
        title: title.trim(),
        description: description.trim(),
        price: priceType === "free" ? 0 : Number.isFinite(parsed) ? parsed : 0,
        priceType,
        condition,
        categoryId,
        latitude: gps?.latitude ?? null,
        longitude: gps?.longitude ?? null,
      });
      if (file) await addImage.mutateAsync({ listingId: listing.id, file });
      tap("medium");
      onDone(listing.id);
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : t("errorLoad"));
    }
  }

  async function grabGps() {
    try {
      setGps(await askPosition());
      setError(null);
    } catch {
      setError(t("gpsError"));
    }
  }

  // Telegram'da e'lonni joylash pastdagi MainButton orqali bajariladi.
  useEffect(
    () =>
      mainButton({
        text: busy ? t("saveDraft") : t("publish"),
        visible: true,
        enabled: !busy,
        progress: busy,
        onClick: submit,
      }),
    // submit har render'da yangi funksiya — unga kiradigan qiymatlar ro'yxatda.
    [busy, t, title, description, price, priceType, condition, categoryId, file, gps],
  );

  if (!list.length && categories.isPending) return <Notice text={t("loading")} />;

  return (
    <div className="screen form">
      <div className="sub-head">
        <button type="button" className="back" onClick={onBack}>
          ‹ {t("back")}
        </button>
      </div>

      <h1 className="screen-title">{t("createTitle")}</h1>

      <label className="field">
        <span className="field-label">{t("titleLabel")}</span>
        <input value={title} maxLength={100} onChange={(event) => setTitle(event.target.value)} />
      </label>

      <label className="field">
        <span className="field-label">{t("descriptionLabel")}</span>
        <textarea
          rows={4}
          value={description}
          maxLength={1000}
          onChange={(event) => setDescription(event.target.value)}
        />
      </label>

      <div className="field">
        <span className="field-label">{t("categoryLabel")}</span>
        <ChipRow>
          {list.map((category) => (
            <Chip
              key={category.id}
              active={categoryId === category.id}
              onClick={() => setCategoryId(category.id)}
            >
              {lang === "uz" ? category.name_uz : category.name_ru}
            </Chip>
          ))}
        </ChipRow>
      </div>

      <div className="field">
        <span className="field-label">{t("priceLabel")}</span>
        <div className="row">
          <input
            inputMode="numeric"
            value={price}
            disabled={priceType === "free"}
            onChange={(event) => setPrice(event.target.value)}
          />
          <ChipRow>
            <Chip active={priceType === "fixed"} onClick={() => setPriceType("fixed")}>
              {t("priceFixed")}
            </Chip>
            <Chip active={priceType === "negotiable"} onClick={() => setPriceType("negotiable")}>
              {t("negotiable")}
            </Chip>
            <Chip
              active={priceType === "free"}
              onClick={() => {
                setPriceType("free");
                setPrice("");
              }}
            >
              {t("free")}
            </Chip>
          </ChipRow>
        </div>
      </div>

      <div className="field">
        <span className="field-label">{t("conditionLabel")}</span>
        <ChipRow>
          <Chip active={condition === "used"} onClick={() => setCondition("used")}>
            {t("conditionUsed")}
          </Chip>
          <Chip active={condition === "new"} onClick={() => setCondition("new")}>
            {t("conditionNew")}
          </Chip>
        </ChipRow>
      </div>

      <div className="field">
        <span className="field-label">{t("photoLabel")}</span>
        <input type="file" accept="image/*" onChange={(event) => pickFile(event.target.files?.[0] ?? null)} />
        {file && (
          <div className="photo-preview">
            <img src={URL.createObjectURL(file)} alt="" />
            <button type="button" className="link" onClick={() => pickFile(null)}>
              {t("removePhoto")}
            </button>
          </div>
        )}
      </div>

      <div className="field">
        <span className="field-label">{t("locationLabel")}</span>
        <ChipRow>
          <Chip active={gps === null} onClick={() => setGps(null)}>
            {t("useProfile")}
          </Chip>
          <Chip active={gps !== null} onClick={grabGps}>
            {t("useGps")}
          </Chip>
        </ChipRow>
        <p className="note">
          {gps ? `${gps.latitude.toFixed(4)}, ${gps.longitude.toFixed(4)}` : t("useProfileHint")}
        </p>
      </div>

      {error && <p className="error">{error}</p>}

      {/* Telegram'da bu ish pastdagi MainButton'ga o'tadi — ikki marta ko'rsatmaymiz. */}
      {!hasMainButton() && (
        <button type="button" className="btn btn-primary" disabled={busy} onClick={submit}>
          {busy ? t("saveDraft") : t("publish")}
        </button>
      )}
    </div>
  );
}
