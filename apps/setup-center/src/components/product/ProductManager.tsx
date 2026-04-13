import React, { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Plus, Package, Loader2 } from "lucide-react";
import { ProductCard } from "./ProductCard";
import { ProductModal, type ProductModalFinishValues } from "./ProductModal";
import { RepoUpdateDialog } from "./RepoUpdateDialog";
import { ProductDetail } from "./ProductDetail";
import {
  Product,
  Repository,
  MOCK_PRODUCTS,
  DEFAULT_ICONS,
  prodInfoWireToProduct,
  applyProcessPayloadToProduct,
  mergeRepositoriesWithProcess,
  buildAnalysisFieldsFromProcessPayload,
} from "./types";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { toast } from "sonner";
import { IS_TAURI } from "@/platform";
import {
  getProdInfo,
  insertProdInfo,
  updateProdInfo,
  getProdProcessInfo,
} from "@/api/rdUnifiedService";
import type { ProdProcessDataPayload } from "@/api/rdUnifiedService";
import "./product-workbench.css";

export function ProductManager({ synapseApiBase = "http://127.0.0.1:18900" }: { synapseApiBase?: string }) {
  const { t } = useTranslation();
  const [products, setProducts] = useState<Product[]>(() => (IS_TAURI ? [] : MOCK_PRODUCTS));
  const [listLoading, setListLoading] = useState(IS_TAURI);

  useEffect(() => {
    if (!IS_TAURI) return;
    let cancelled = false;
    (async () => {
      try {
        const resp = await getProdInfo(synapseApiBase);
        if (cancelled) return;
        const rows = Array.isArray(resp.data) ? resp.data : [];
        const mapped = rows.map(prodInfoWireToProduct);
        if (resp.total !== rows.length) {
          console.warn("[get_prod_info] total != data.length", resp.total, rows.length);
        }
        setProducts(mapped);
      } catch (e) {
        if (cancelled) return;
        const msg = e instanceof Error ? e.message : String(e);
        if (msg === "missing_devservice_ip") {
          toast.error(t("workbench.products.createMissingDevservice"));
        } else {
          toast.error(t("workbench.products.loadListFailed", { message: msg }));
        }
        setProducts([]);
      } finally {
        if (!cancelled) setListLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [synapseApiBase, t]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingProduct, setEditingProduct] = useState<Product | undefined>(undefined);
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);
  const [isDetailOpen, setIsDetailOpen] = useState(false);
  const [cardActionBusy, setCardActionBusy] = useState<{
    productId: string;
    kind: "refresh" | "repo";
  } | null>(null);

  const filteredProducts = products;

  const mergeProcessIntoProduct = (productId: string, payload: ProdProcessDataPayload) => {
    setProducts((prev) =>
      prev.map((p) => (p.id === productId ? applyProcessPayloadToProduct(p, payload) : p)),
    );
    setSelectedProduct((sp) =>
      sp?.id === productId ? applyProcessPayloadToProduct(sp, payload) : sp,
    );
  };

  const handleRefreshProcess = async (product: Product) => {
    if (!IS_TAURI) {
      toast.message(t("workbench.products.tauriOnlyAction"));
      return;
    }
    setCardActionBusy({ productId: product.id, kind: "refresh" });
    try {
      const resp = await getProdProcessInfo(synapseApiBase, { prod: product.name.trim() });
      if (resp.data == null) {
        toast.error(t("workbench.products.refreshProcessEmpty"));
        return;
      }
      mergeProcessIntoProduct(product.id, resp.data);
      toast.success(t("workbench.products.refreshProcessSuccess"));
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e);
      if (msg === "missing_devservice_ip") {
        toast.error(t("workbench.products.createMissingDevservice"));
      } else {
        toast.error(t("workbench.products.refreshProcessFailed", { message: msg }));
      }
    } finally {
      setCardActionBusy(null);
    }
  };

  const [repoDialogProduct, setRepoDialogProduct] = useState<Product | null>(null);

  const handleOpenRepoUpdate = (product: Product) => {
    if (!IS_TAURI) {
      toast.message(t("workbench.products.tauriOnlyAction"));
      return;
    }
    setRepoDialogProduct(product);
  };

  const handleRepoUpdateSuccess = (
    productId: string,
    repositories: Repository[],
    process: ProdProcessDataPayload | null | undefined,
  ) => {
    setProducts((prev) =>
      prev.map((p) => {
        if (p.id !== productId) return p;
        const mergedRepos = mergeRepositoriesWithProcess(repositories, process?.repo_process);
        if (process == null) {
          return { ...p, repositories: mergedRepos };
        }
        const fields = buildAnalysisFieldsFromProcessPayload(process);
        return {
          ...p,
          repositories: mergedRepos,
          analysisStatus: fields.analysisStatus,
          analysisUnified: fields.analysisUnified,
          analysisTimes: fields.analysisTimes,
        };
      }),
    );
    setSelectedProduct((sp) => {
      if (sp?.id !== productId) return sp;
      const mergedRepos = mergeRepositoriesWithProcess(repositories, process?.repo_process);
      if (process == null) {
        return { ...sp, repositories: mergedRepos };
      }
      const fields = buildAnalysisFieldsFromProcessPayload(process);
      return {
        ...sp,
        repositories: mergedRepos,
        analysisStatus: fields.analysisStatus,
        analysisUnified: fields.analysisUnified,
        analysisTimes: fields.analysisTimes,
      };
    });
  };

  const handleAdd = () => {
    setEditingProduct(undefined);
    setIsModalOpen(true);
  };

  const handleEdit = (product: Product) => {
    setEditingProduct(product);
    setIsModalOpen(true);
  };

  const handleDelete = (id: string) => {
    setProducts(products.filter((p) => p.id !== id));
    toast.success(t("workbench.products.deleted") || "已删除");
  };

  const handleView = (product: Product) => {
    setSelectedProduct(product);
    setIsDetailOpen(true);
  };

  const handleFinish = async (values: ProductModalFinishValues) => {
    if (editingProduct) {
      if (IS_TAURI) {
        try {
          await updateProdInfo(synapseApiBase, {
            prod: editingProduct.name.trim(),
            function: (values.features || "").trim(),
            prod_icon: (values.iconLabel || "").trim(),
            prod_desc: (values.description || "").trim(),
          });
        } catch (e) {
          const msg = e instanceof Error ? e.message : String(e);
          if (msg === "missing_devservice_ip") {
            toast.error(t("workbench.products.createMissingDevservice"));
          } else if (/userinfo|未找到/.test(msg)) {
            toast.error(t("workbench.products.createMissingUserinfo"));
          } else {
            toast.error(t("workbench.products.updateRemoteFailed", { message: msg }));
          }
          return;
        }
      }

      setProducts(
        products.map((p) =>
          p.id === editingProduct.id
            ? ({
                ...p,
                ...values,
                name: p.name,
                repositories: p.repositories,
                icon: values.icon ?? p.icon,
              } as Product)
            : p,
        ),
      );
      toast.success(t("workbench.products.updated") || "已更新");
      setIsModalOpen(false);
      return;
    }

    if (IS_TAURI) {
      try {
        await insertProdInfo(synapseApiBase, {
          prod: values.name || "",
          version: (values.versionCode || values.version || "").trim(),
          module: (values.module || "").trim(),
          space: (values.spaceLabel || "").trim(),
          function: values.features || "",
          prod_icon: (values.iconLabel || "").trim(),
          prod_desc: (values.description || "").trim(),
          repo_info: (values.repositories || []).map((r) => ({
            repo_url: r.url,
            repo_branch: r.branch,
            repo_func: r.purpose,
            repo_token: r.token || "",
            repo_master: r.isMain ? "Y" : "N",
          })),
        });
      } catch (e) {
        const msg = e instanceof Error ? e.message : String(e);
        if (msg === "missing_devservice_ip") {
          toast.error(t("workbench.products.createMissingDevservice"));
        } else if (/userinfo|未找到/.test(msg)) {
          toast.error(t("workbench.products.createMissingUserinfo"));
        } else {
          toast.error(t("workbench.products.createRemoteFailed", { message: msg }));
        }
        return;
      }
    }

    const newProduct: Product = {
      ...values,
      id: Math.random().toString(36).slice(2, 11),
      icon: values.icon || DEFAULT_ICONS[Math.floor(Math.random() * DEFAULT_ICONS.length)].value,
      repositories: values.repositories || [],
      knowledge: values.knowledge || {
        architecture: false,
        solution: false,
        requirements: false,
        manual: false,
        delivery: false,
      },
      analysisStatus: {
        code: "pending",
        ticket: "pending",
        document: "pending",
      },
      analysisUnified: {
        code: "new",
        ticket: "new",
        document: "new",
      },
      analysisTimes: {},
    } as Product;
    setProducts([newProduct, ...products]);
    toast.success(t("workbench.products.created") || "已创建");
    setIsModalOpen(false);
  };

  return (
    <div className="product-workbench">
      <div className="product-workbench-scroll">
        <div className="mx-auto flex w-full max-w-6xl flex-col gap-5">
          {/* Header Card matching MCP */}
          <Card className="gap-0 overflow-hidden border-border/80 bg-gradient-to-br from-primary/5 via-background to-background py-0 shadow-sm">
            <CardHeader className="gap-3 px-6 py-5">
              <div className="flex items-start justify-between gap-4">
                <div className="flex min-w-0 items-start gap-4">
                  <div className="flex size-12 shrink-0 items-center justify-center rounded-2xl bg-primary/10 text-primary">
                    <Package size={22} />
                  </div>
                  <div className="min-w-0 space-y-2">
                    <div className="flex min-w-0 items-center gap-3">
                      <CardTitle className="truncate text-xl tracking-tight">
                        {t("workbench.products.breadcrumbCurrent")}
                      </CardTitle>
                    </div>
                    <CardDescription className="max-w-3xl text-sm leading-6">
                      {t("workbench.products.subtitle")}
                    </CardDescription>
                  </div>
                </div>

                <div className="flex shrink-0 items-center gap-2">
                  <Button variant="outline" onClick={handleAdd}>
                    <Plus size={14} className="mr-1.5" />
                    {t("workbench.products.addProduct")}
                  </Button>
                </div>
              </div>
            </CardHeader>
          </Card>

          {/* Product Grid — get_prod_info 全量拉取，不做分页 */}
          {listLoading ? (
            <Card className="shadow-sm border-border/80">
              <CardContent className="flex flex-col items-center justify-center gap-3 py-16 text-muted-foreground">
                <Loader2 className="size-10 animate-spin text-primary/80" />
                <p className="text-sm">{t("workbench.products.loadingList")}</p>
              </CardContent>
            </Card>
          ) : filteredProducts.length > 0 ? (
            <div className="grid gap-5 sm:grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
              {filteredProducts.map((product) => (
                <ProductCard
                  key={product.id}
                  product={product}
                  onEdit={handleEdit}
                  onDelete={handleDelete}
                  onView={handleView}
                  onRefreshProcess={handleRefreshProcess}
                  onChangeRepos={handleOpenRepoUpdate}
                  cardActionBusy={cardActionBusy}
                />
              ))}
            </div>
          ) : (
            <Card className="shadow-sm border-border/80">
              <CardContent className="py-12 text-center text-muted-foreground">
                <div className="flex flex-col items-center justify-center gap-3 opacity-60">
                  <Package size={48} className="text-muted-foreground" />
                  <p className="text-base font-medium">{t("workbench.products.empty")}</p>
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        <ProductModal
          open={isModalOpen}
          onCancel={() => setIsModalOpen(false)}
          onFinish={handleFinish}
          initialValues={editingProduct}
        />

        {/* 更新仓库：内部调用 changeRepoInfo → :10001/dev/iwhalecloud/synapse/change_repo_info */}
        <RepoUpdateDialog
          open={repoDialogProduct != null}
          onOpenChange={(o) => {
            if (!o) setRepoDialogProduct(null);
          }}
          product={repoDialogProduct}
          synapseApiBase={synapseApiBase}
          onSuccess={handleRepoUpdateSuccess}
          onBusyChange={(busy) => {
            if (busy && repoDialogProduct) {
              setCardActionBusy({ productId: repoDialogProduct.id, kind: "repo" });
            } else {
              setCardActionBusy(null);
            }
          }}
        />

        <ProductDetail product={selectedProduct} open={isDetailOpen} onClose={() => setIsDetailOpen(false)} />
      </div>
    </div>
  );
}
