import React, { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Loader2, Plus, Trash2 } from "lucide-react";
import { Product, Repository, productRepositoriesToRdRepoInfo } from "./types";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
import { IS_TAURI } from "@/platform";
import { changeRepoInfo, getProdProcessInfo } from "@/api/rdUnifiedService";
import type { ProdProcessDataPayload } from "@/api/rdUnifiedService";

export type RepoUpdateDialogProps = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  product: Product | null;
  synapseApiBase: string;
  onSuccess: (productId: string, repositories: Repository[], process?: ProdProcessDataPayload | null) => void;
  onBusyChange?: (busy: boolean) => void;
};

/** 带稳定 key；服务端已有仓库 branchLocked=true，新增行可填分支 */
type RepoEditRow = Repository & {
  clientKey: string;
  branchLocked: boolean;
};

let keySeq = 0;
function nextKey(prefix: string): string {
  keySeq += 1;
  return `${prefix}-${Date.now()}-${keySeq}`;
}

function fromProductRepos(repos: Repository[]): RepoEditRow[] {
  return repos.map((r, i) => ({
    ...r,
    clientKey: nextKey(`s-${i}`),
    branchLocked: true,
  }));
}

function toRepository(r: RepoEditRow): Repository {
  const { clientKey: _k, branchLocked: _b, ...rest } = r;
  return rest;
}

function toRepositories(rows: RepoEditRow[]): Repository[] {
  return rows.map(toRepository);
}

export function RepoUpdateDialog({
  open,
  onOpenChange,
  product,
  synapseApiBase,
  onSuccess,
  onBusyChange,
}: RepoUpdateDialogProps) {
  const { t } = useTranslation();
  const [rows, setRows] = useState<RepoEditRow[]>([]);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (open && product) {
      setRows(fromProductRepos(product.repositories));
    }
  }, [open, product]);

  const updateRow = (index: number, patch: Partial<Repository>) => {
    setRows((prev) => {
      const next = prev.map((r) => ({ ...r }));
      if (patch.isMain === true) {
        for (let i = 0; i < next.length; i++) {
          next[i] = { ...next[i], isMain: i === index };
        }
      } else {
        next[index] = { ...next[index], ...patch };
      }
      return next;
    });
  };

  const addRow = () => {
    setRows((prev) => {
      const isFirst = prev.length === 0;
      const row: RepoEditRow = {
        url: "",
        branch: "",
        purpose: "",
        token: "",
        isMain: isFirst,
        clientKey: nextKey("n"),
        branchLocked: false,
      };
      return [...prev, row];
    });
  };

  const removeRow = (index: number) => {
    setRows((prev) => {
      const removed = prev[index];
      const next = prev.filter((_, i) => i !== index);
      if (removed.isMain && next.length > 0) {
        next[0] = { ...next[0], isMain: true };
      }
      return next;
    });
  };

  const handleSave = async () => {
    if (!product || !IS_TAURI) return;
    const plain = toRepositories(rows);
    if (plain.length > 0) {
      const mains = plain.filter((r) => r.isMain);
      if (mains.length === 0) {
        toast.error(t("workbench.products.modal.mainRepoErrorNone"));
        return;
      }
      if (mains.length > 1) {
        toast.error(t("workbench.products.modal.mainRepoErrorMany"));
        return;
      }
      const incomplete = plain.some(
        (r) => !r.url.trim() || !r.branch.trim(),
      );
      if (incomplete) {
        toast.error(t("workbench.products.repoUpdateDialog.incompleteRepo"));
        return;
      }
    }

    setSaving(true);
    onBusyChange?.(true);
    try {
      const temp: Product = { ...product, repositories: plain };
      await changeRepoInfo(synapseApiBase, {
        prod: product.name.trim(),
        repo_info: productRepositoriesToRdRepoInfo(temp),
      });
      toast.success(t("workbench.products.changeRepoSuccess"));
      let process: ProdProcessDataPayload | null = null;
      try {
        const resp = await getProdProcessInfo(synapseApiBase, { prod: product.name.trim() });
        process = resp.data;
      } catch {
        /* optional */
      }
      onSuccess(product.id, plain.map((r) => ({ ...r })), process);
      onOpenChange(false);
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e);
      if (msg === "missing_devservice_ip") {
        toast.error(t("workbench.products.createMissingDevservice"));
      } else {
        toast.error(t("workbench.products.changeRepoFailed", { message: msg }));
      }
    } finally {
      setSaving(false);
      onBusyChange?.(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[640px] max-h-[85vh] flex flex-col gap-0 p-0">
        <DialogHeader className="px-6 py-4 border-b border-border/60">
          <DialogTitle>{t("workbench.products.repoUpdateDialog.title")}</DialogTitle>
          <p className="text-sm text-muted-foreground m-0 pt-1">{t("workbench.products.repoUpdateDialog.desc")}</p>
        </DialogHeader>

        <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4 custom-scrollbar">
          <div className="flex justify-end">
            <Button type="button" variant="outline" size="sm" onClick={addRow} disabled={saving}>
              <Plus size={14} className="mr-1.5" />
              {t("workbench.products.repoUpdateDialog.addRepo")}
            </Button>
          </div>

          {rows.length === 0 ? (
            <p className="text-sm text-muted-foreground">{t("workbench.products.repoUpdateDialog.empty")}</p>
          ) : (
            rows.map((repo, index) => (
              <div
                key={repo.clientKey}
                className="rounded-lg border border-border/80 bg-muted/10 p-4 space-y-3"
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="text-sm font-medium">
                    {t("workbench.products.modal.repoConfigN", { n: index + 1 })}
                  </span>
                  <div className="flex items-center gap-2">
                    {repo.isMain && (
                      <Badge variant="secondary" className="text-[10px] font-normal bg-blue-500/10 text-blue-700 dark:text-blue-400">
                        {t("workbench.products.modal.mainRepo")}
                      </Badge>
                    )}
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8 text-destructive hover:text-destructive"
                      disabled={saving}
                      onClick={() => removeRow(index)}
                      title={t("workbench.products.repoUpdateDialog.removeRepo")}
                    >
                      <Trash2 size={14} />
                    </Button>
                  </div>
                </div>

                <div className="grid gap-3 sm:grid-cols-2">
                  <div className="space-y-1.5 sm:col-span-2">
                    <Label className="text-xs">{t("workbench.products.modal.branch")}</Label>
                    <Input
                      readOnly={repo.branchLocked}
                      tabIndex={repo.branchLocked ? -1 : undefined}
                      value={repo.branch}
                      onChange={(e) => {
                        if (!repo.branchLocked) updateRow(index, { branch: e.target.value });
                      }}
                      className={`h-9 text-xs ${repo.branchLocked ? "bg-muted/50 cursor-default" : ""}`}
                      placeholder={t("workbench.products.modal.branchPlaceholder")}
                    />
                    <p className="text-[11px] text-muted-foreground m-0">
                      {repo.branchLocked
                        ? t("workbench.products.repoUpdateDialog.branchHint")
                        : t("workbench.products.repoUpdateDialog.branchEditableHint")}
                    </p>
                  </div>
                  <div className="space-y-1.5 sm:col-span-2">
                    <Label className="text-xs">{t("workbench.products.modal.url")}</Label>
                    <Input
                      className="h-9 text-xs"
                      value={repo.url}
                      onChange={(e) => updateRow(index, { url: e.target.value })}
                      placeholder={t("workbench.products.modal.urlPlaceholder")}
                    />
                  </div>
                  <div className="space-y-1.5 sm:col-span-2">
                    <Label className="text-xs">{t("workbench.products.modal.purpose")}</Label>
                    <Input
                      className="h-9 text-xs"
                      value={repo.purpose}
                      onChange={(e) => updateRow(index, { purpose: e.target.value })}
                      placeholder={t("workbench.products.modal.purposePlaceholder")}
                    />
                  </div>
                  <div className="space-y-1.5 sm:col-span-2">
                    <Label className="text-xs">{t("workbench.products.modal.token")}</Label>
                    <Input
                      className="h-9 text-xs"
                      type="password"
                      value={repo.token || ""}
                      onChange={(e) => updateRow(index, { token: e.target.value })}
                      placeholder={t("workbench.products.modal.tokenPlaceholder")}
                    />
                  </div>
                  <div className="flex items-center gap-2 sm:col-span-2 pt-1">
                    <Switch
                      checked={repo.isMain}
                      onCheckedChange={(c) => updateRow(index, { isMain: c })}
                      id={`repo-main-dialog-${repo.clientKey}`}
                    />
                    <Label htmlFor={`repo-main-dialog-${repo.clientKey}`} className="text-xs cursor-pointer">
                      {t("workbench.products.modal.mainRepo")}
                    </Label>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>

        <DialogFooter className="px-6 py-4 border-t border-border/60 bg-muted/10">
          <Button type="button" variant="outline" onClick={() => onOpenChange(false)} disabled={saving}>
            {t("workbench.products.modal.cancel")}
          </Button>
          <Button type="button" onClick={() => void handleSave()} disabled={saving || !product}>
            {saving ? <Loader2 className="size-4 animate-spin mr-2" /> : null}
            {t("workbench.products.repoUpdateDialog.save")}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
