// Profil: ism, ishonchi ballari, hudud va GPS joylashuvini yangilash.

import { useState } from "react";
import { useDistricts, useSetLocation } from "../api/hooks";
import type { Profile as ProfileType } from "../api/types";
import { useLang } from "../lib/i18n";
import { askPosition } from "../lib/geo";
import { tap } from "../lib/telegram";

export function Profile({
  profile,
  onMyListings,
}: {
  profile: ProfileType;
  onMyListings: () => void;
}) {
  const { t, lang } = useLang();
  const districts = useDistricts();
  const setLocation = useSetLocation();

  const district = districts.data?.find((item) => item.id === profile.district_id);
  const districtName = district ? (lang === "uz" ? district.name_uz : district.name_ru) : t("empty");

  const [denied, setDenied] = useState(false);

  async function refreshLocation() {
    tap("medium");
    try {
      setDenied(false);
      setLocation.mutate(await askPosition());
    } catch {
      setDenied(true);
    }
  }

  return (
    <div className="screen">
      <div className="profile-head">
        <div className="avatar big">{profile.display_name.slice(0, 1)}</div>
        <div>
          <h1 className="profile-name">{profile.display_name}</h1>
          {profile.username && <p className="note">@{profile.username}</p>}
        </div>
      </div>

      <dl className="info">
        <div>
          <dt>{t("trust")}</dt>
          <dd>{profile.trust_score}</dd>
        </div>
        <div>
          <dt>{t("homeDistrict")}</dt>
          <dd>{districtName}</dd>
        </div>
        <div>
          <dt>{t("languageLabel")}</dt>
          <dd>{lang === "uz" ? "O'zbekcha" : "Русский"}</dd>
        </div>
      </dl>

      <div className="actions column">
        <button type="button" className="btn btn-primary" onClick={onMyListings}>
          {t("mine")}
        </button>
        <button
          type="button"
          className="btn btn-ghost"
          disabled={setLocation.isPending}
          onClick={refreshLocation}
        >
          {t("useGps")}
        </button>
        {denied && <p className="error">{t("gpsError")}</p>}
        {setLocation.isError && <p className="error">{String(setLocation.error.message)}</p>}
        <p className="note">
          {t("notifications")}: {t("soon")}
        </p>
      </div>
    </div>
  );
}
