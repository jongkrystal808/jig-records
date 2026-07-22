import { auditApi } from "./api/auditClient";
import { authApi } from "./api/authClient";
import { inventoryApi } from "./api/inventoryClient";
import { fetchFixtureImageObjectUrl, fixtureImageUrlByCode, mediaApi } from "./api/mediaClient";
import { masterApi } from "./api/masterClient";
import { productionApi } from "./api/productionClient";
import { searchApi } from "./api/searchClient";

// Keep the public API surface stable while the implementation is split by domain underneath.
export const api = {
  ...auditApi,
  ...authApi,
  ...mediaApi,
  ...masterApi,
  ...inventoryApi,
  ...productionApi,
  ...searchApi
};

export { fetchFixtureImageObjectUrl, fixtureImageUrlByCode };
