type ApiErrorDetail = {
  error?: {
    message?: string;
    type?: string;
    details?: Array<{ field?: string; message?: string }>;
  };
  detail?:
    | string
    | Array<{
        loc?: Array<string | number>;
        msg?: string;
        type?: string;
      }>;
  message?: string;
};

function formatValidationDetails(details: Array<{ loc?: Array<string | number>; msg?: string; type?: string }>): string {
  const messages = details
    .map((item) => {
      const field = item.loc?.filter((part) => typeof part === "string").join(".") || "";
      const message = item.msg || item.type || "";
      if (field && message) return `${field}: ${message}`;
      return field || message;
    })
    .filter(Boolean);
  return messages.join("；");
}

export function extractErrorMessage(body: string, fallback: string): string {
  if (!body) {
    return fallback;
  }

  try {
    const parsed = JSON.parse(body) as ApiErrorDetail;
    if (typeof parsed?.error?.message === "string" && parsed.error.message) {
      return parsed.error.message;
    }
    if (Array.isArray(parsed?.detail) && parsed.detail.length > 0) {
      const formatted = formatValidationDetails(parsed.detail);
      if (formatted) return formatted;
    }
    if (typeof parsed?.detail === "string" && parsed.detail) {
      return parsed.detail;
    }
    if (typeof parsed?.message === "string" && parsed.message) {
      return parsed.message;
    }
  } catch {
    return body.length > 240 ? `${body.slice(0, 237)}...` : body;
  }

  return fallback;
}
