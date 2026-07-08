import type { AuditLogEntry } from "@/types";

import { request } from "@/api/core";

export const auditApi = {
  listAuditLogs(customerId?: number, limit = 3) {
    return request<AuditLogEntry[]>(
      customerId ? `/audit/logs?customer_id=${customerId}&limit=${limit}` : `/audit/logs?limit=${limit}`
    );
  }
};
