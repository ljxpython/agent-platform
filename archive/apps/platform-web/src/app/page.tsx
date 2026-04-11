"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { ensureOidcSession } from "@/lib/oidc-storage";


export default function Page() {
  const router = useRouter();

  useEffect(() => {
    let cancelled = false;

    void ensureOidcSession().then((loggedIn) => {
      if (cancelled) {
        return;
      }
      if (loggedIn) {
        router.replace("/workspace/projects");
        return;
      }
      router.replace("/auth/login");
    });

    return () => {
      cancelled = true;
    };
  }, [router]);

  return null;
}
