"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useEffect } from "react";

export default function RuntimeIndexPage() {
  const router = useRouter();
  const searchParams = useSearchParams();

  useEffect(() => {
    const query = searchParams.toString();
    router.replace(query ? `/workspace/runtime/models?${query}` : "/workspace/runtime/models");
  }, [router, searchParams]);

  return <div className="p-6 text-sm text-muted-foreground">Redirecting to Runtime workspace...</div>;
}
