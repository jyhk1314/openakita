import React, { useEffect, useState, useRef } from "react";
import { useTranslation } from "react-i18next";
import { Trash2, GitBranch, ChevronRight, Plus, X } from 'lucide-react';
import { Product, Repository, DEFAULT_ICONS } from "./types";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
import "./product-workbench.css";

const mockProjectSpaces = [
  { label: '基础平台部', value: 'space_1' },
  { label: '业务中台部', value: 'space_2' },
  { label: '数据智能部', value: 'space_3' },
];

const mockProductVersions = [
  { label: 'V1.0.0', value: 'v1.0.0' },
  { label: 'V2.0.0', value: 'v2.0.0' },
  { label: 'V3.0.0', value: 'v3.0.0' },
  { label: 'V4.0.0', value: 'v4.0.0' },
];

const mockModules: Record<string, { label: string; value: string }[]> = {
  'v1.0.0': [
    { label: '用户管理模块', value: 'mod_user' },
    { label: '权限管理模块', value: 'mod_auth' },
    { label: '日志审计模块', value: 'mod_log' },
  ],
  'v2.0.0': [
    { label: '订单管理模块', value: 'mod_order' },
    { label: '支付管理模块', value: 'mod_pay' },
    { label: '库存管理模块', value: 'mod_inventory' },
  ],
  'v3.0.0': [
    { label: '数据分析模块', value: 'mod_analytics' },
    { label: '报表中心模块', value: 'mod_report' },
    { label: 'AI 推荐模块', value: 'mod_ai' },
  ],
  'v4.0.0': [
    { label: '消息通知模块', value: 'mod_notify' },
    { label: '工作流引擎模块', value: 'mod_workflow' },
    { label: '监控告警模块', value: 'mod_monitor' },
  ],
};

const mockRepos: Record<string, { name: string; url: string; branch: string }[]> = {
  'mod_user': [
    { name: 'user-backend', url: 'https://git-nj.iwhalecloud.com/backend/user-backend.git', branch: 'master' },
    { name: 'user-frontend', url: 'https://git-nj.iwhalecloud.com/frontend/user-frontend.git', branch: 'develop' },
  ],
  'mod_auth': [
    { name: 'auth-service', url: 'https://git-nj.iwhalecloud.com/backend/auth-service.git', branch: 'develop' },
    { name: 'auth-gateway', url: 'https://git-nj.iwhalecloud.com/backend/auth-gateway.git', branch: 'master' },
  ],
  'mod_log': [
    { name: 'log-collector', url: 'https://git-nj.iwhalecloud.com/backend/log-collector.git', branch: 'master' },
  ],
  'mod_order': [
    { name: 'order-service', url: 'https://git-nj.iwhalecloud.com/backend/order-service.git', branch: 'master' },
    { name: 'order-frontend', url: 'https://git-nj.iwhalecloud.com/frontend/order-frontend.git', branch: 'develop' },
  ],
  'mod_pay': [
    { name: 'pay-service', url: 'https://git-nj.iwhalecloud.com/backend/pay-service.git', branch: 'master' },
  ],
  'mod_inventory': [
    { name: 'inventory-service', url: 'https://git-nj.iwhalecloud.com/backend/inventory-service.git', branch: 'master' },
  ],
  'mod_analytics': [
    { name: 'analytics-engine', url: 'https://git-nj.iwhalecloud.com/data/analytics-engine.git', branch: 'develop' },
    { name: 'analytics-frontend', url: 'https://git-nj.iwhalecloud.com/frontend/analytics-frontend.git', branch: 'develop' },
  ],
  'mod_report': [
    { name: 'report-service', url: 'https://git-nj.iwhalecloud.com/backend/report-service.git', branch: 'master' },
  ],
  'mod_ai': [
    { name: 'ai-recommend', url: 'https://git-nj.iwhalecloud.com/ai/ai-recommend.git', branch: 'develop' },
    { name: 'ai-model-server', url: 'https://git-nj.iwhalecloud.com/ai/ai-model-server.git', branch: 'main' },
  ],
  'mod_notify': [
    { name: 'notify-service', url: 'https://git-nj.iwhalecloud.com/backend/notify-service.git', branch: 'master' },
  ],
  'mod_workflow': [
    { name: 'workflow-engine', url: 'https://git-nj.iwhalecloud.com/backend/workflow-engine.git', branch: 'develop' },
    { name: 'workflow-frontend', url: 'https://git-nj.iwhalecloud.com/frontend/workflow-frontend.git', branch: 'develop' },
  ],
  'mod_monitor': [
    { name: 'monitor-agent', url: 'https://git-nj.iwhalecloud.com/ops/monitor-agent.git', branch: 'master' },
  ],
};

const checkProductExists = async (space: string, version: string, module: string) => {
  return new Promise(resolve => {
    setTimeout(() => {
      resolve(space === 'space_1' && version === 'v1.0.0' && module === 'mod_user');
    }, 300);
  });
};

export type ProductModalFinishValues = Partial<Product> & {
  /** 项目空间展示名 */
  spaceLabel?: string;
  /** 版本选项值，如 v1.0.0 */
  versionCode?: string;
  /** 模块选项值，如 mod_user */
  moduleCode?: string;
  /** 图标选项文案（供研发统一服务 prod_icon） */
  iconLabel?: string;
};

interface ProductModalProps {
  open: boolean;
  onCancel: () => void;
  onFinish: (values: ProductModalFinishValues) => void | Promise<void>;
  initialValues?: Product;
}

export function ProductModal({ open, onCancel, onFinish, initialValues }: ProductModalProps) {
  const { t } = useTranslation();
  const [isEdit, setIsEdit] = useState(false);
  
  const [formState, setFormState] = useState<{
    name: string;
    icon: string;
    projectSpace: string;
    productVersion: string;
    appModule: string;
    description: string;
    features: string[];
    repositories: Repository[];
  }>({
    name: "",
    icon: DEFAULT_ICONS[0].value,
    projectSpace: "",
    productVersion: "",
    appModule: "",
    description: "",
    features: [],
    repositories: []
  });

  const [projectSpaces, setProjectSpaces] = useState<{label: string, value: string}[]>([]);
  const [productVersions, setProductVersions] = useState<{label: string, value: string}[]>([]);
  const [appModules, setAppModules] = useState<{label: string, value: string}[]>([]);
  const [expandedRepos, setExpandedRepos] = useState<string[]>([]);

  const isProductInfoFilled = !!(formState.name && formState.projectSpace && formState.productVersion && formState.appModule);

  useEffect(() => {
    if (open) {
      setProjectSpaces(mockProjectSpaces);
      setProductVersions(mockProductVersions);
      
      if (initialValues) {
        const pv = initialValues.version ?? "";
        setAppModules(mockModules[pv] || []);
        setFormState({
          name: initialValues.name || "",
          icon: initialValues.icon || DEFAULT_ICONS[0].value,
          projectSpace: initialValues.space ?? "",
          productVersion: pv,
          appModule: initialValues.module ?? "",
          description: initialValues.description || "",
          features: initialValues.features ? initialValues.features.split(",") : [],
          repositories: initialValues.repositories || [],
        });
        setIsEdit(true);
      } else {
        setFormState({
          name: "",
          icon: DEFAULT_ICONS[0].value,
          projectSpace: "",
          productVersion: "",
          appModule: "",
          description: "",
          features: [],
          repositories: []
        });
        setIsEdit(false);
        setAppModules([]);
      }
    }
  }, [open, initialValues]);

  const handleVersionChange = (val: string) => {
    setFormState(prev => ({ ...prev, productVersion: val, appModule: "", repositories: [] }));
    setAppModules(mockModules[val] || []);
  };

  const handleModuleChange = async (val: string) => {
    setFormState(prev => ({ ...prev, appModule: val }));
    if (!isEdit && formState.projectSpace && formState.productVersion && val) {
      const exists = await checkProductExists(formState.projectSpace, formState.productVersion, val);
      if (exists) {
        toast.error(t("workbench.products.modal.duplicateProduct"));
        return;
      }
    }
    const repos = mockRepos[val] || [];
    setFormState(prev => ({
      ...prev,
      repositories: repos.map((r, idx) => ({
        url: r.url,
        branch: r.branch,
        purpose: "",
        token: "",
        isMain: idx === 0,
        analysisTime: "",
        wireAnalysisState: "new" as const,
      }))
    }));
  };

  const updateRepo = (index: number, field: keyof Repository, value: any) => {
    const newRepos = [...formState.repositories];
    if (field === "isMain" && value === true) {
      newRepos.forEach(r => r.isMain = false);
    }
    newRepos[index] = { ...newRepos[index], [field]: value };
    setFormState(prev => ({ ...prev, repositories: newRepos }));
  };

  const removeRepo = (index: number) => {
    const newRepos = formState.repositories.filter((_, i) => i !== index);
    setFormState(prev => ({ ...prev, repositories: newRepos }));
  };

  const addRepo = () => {
    const newRepos = [
      ...formState.repositories,
      {
        branch: "master",
        isMain: formState.repositories.length === 0,
        url: "",
        purpose: "",
        token: "",
        wireAnalysisState: "new" as const,
      },
    ];
    setFormState(prev => ({ ...prev, repositories: newRepos }));
    setExpandedRepos(prev => [...prev, String(newRepos.length - 1)]);
  };

  const toggleRepoExpand = (idx: string) => {
    setExpandedRepos(prev => prev.includes(idx) ? prev.filter(i => i !== idx) : [...prev, idx]);
  };

  const handleSubmit = async () => {
    if (!formState.name) {
      toast.error(t("workbench.products.modal.nameRequired") || "请输入产品名称");
      return;
    }
    if (!isEdit && (!formState.projectSpace || !formState.productVersion || !formState.appModule)) {
      toast.error("请完善项目空间、产品版本和应用模块信息");
      return;
    }
    
    if (!isEdit) {
      const mainRepos = formState.repositories.filter(r => r.isMain);
      if (formState.repositories.length > 0) {
        if (mainRepos.length === 0) {
          toast.error(t("workbench.products.modal.mainRepoErrorNone") || "必须且只能有一个主分支仓库");
          return;
        }
        if (mainRepos.length > 1) {
          toast.error(t("workbench.products.modal.mainRepoErrorMany") || "只能有一个主分支仓库");
          return;
        }
      }
    }

    const versionLabel = isEdit
      ? (formState.productVersion || "")
      : (productVersions.find((v) => v.value === formState.productVersion)?.label ||
        formState.productVersion ||
        "");
    const moduleLabel = isEdit
      ? (formState.appModule || "")
      : (appModules.find((m) => m.value === formState.appModule)?.label || formState.appModule || "");
    const featuresStr = formState.features.join(",");
    const spaceLabel = isEdit
      ? (formState.projectSpace || "")
      : (projectSpaces.find((s) => s.value === formState.projectSpace)?.label || formState.projectSpace || "");
    const iconLabel = DEFAULT_ICONS.find((i) => i.value === formState.icon)?.label || "";

    await Promise.resolve(
      onFinish({
        name: formState.name,
        icon: formState.icon,
        version: versionLabel,
        module: moduleLabel,
        description: formState.description,
        features: featuresStr,
        repositories: formState.repositories,
        spaceLabel,
        versionCode: formState.productVersion,
        moduleCode: formState.appModule,
        iconLabel,
      }),
    );
  };

  return (
    <Dialog open={open} onOpenChange={(val) => { if (!val) onCancel(); }}>
      <DialogContent className="sm:max-w-[800px] p-0 flex flex-col max-h-[85vh] border-border/80 shadow-lg bg-background/95 backdrop-blur">
        <DialogHeader className="px-6 py-4 border-b border-border/60 bg-muted/10">
          <DialogTitle className="text-lg">
            {isEdit ? t("workbench.products.modal.editTitle") : t("workbench.products.modal.createTitle")}
          </DialogTitle>
        </DialogHeader>

        <div className="flex-1 overflow-y-auto px-6 py-5 custom-scrollbar space-y-6">
          {/* Row 1: Name, Icon */}
          <div className="grid grid-cols-12 gap-5">
            <div className="col-span-8 space-y-2">
              <Label>{t("workbench.products.modal.name")} <span className="text-destructive">*</span></Label>
              <Input 
                placeholder={t("workbench.products.modal.namePlaceholder")} 
                maxLength={64} 
                disabled={isEdit}
                value={formState.name}
                onChange={e => setFormState(prev => ({...prev, name: e.target.value}))}
              />
            </div>
            <div className="col-span-4 space-y-2">
              <Label>{t("workbench.products.modal.icon")} <span className="text-destructive">*</span></Label>
              <Select value={formState.icon} onValueChange={v => setFormState(prev => ({...prev, icon: v}))}>
                <SelectTrigger className="w-full">
                  <SelectValue placeholder={t("workbench.products.modal.iconPlaceholder")} />
                </SelectTrigger>
                <SelectContent>
                  {DEFAULT_ICONS.map(icon => (
                    <SelectItem key={icon.label} value={icon.value}>
                      <div className="flex items-center gap-2">
                        <img src={icon.value} alt={icon.label} className="w-5 h-5 rounded object-contain bg-primary/10" />
                        <span>{icon.label}</span>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Row 2: Space, Version, Module — 新建用 mock 下拉；编辑直接展示接口原文（多为中文名，与 Select value 不一致） */}
          <div className="grid grid-cols-12 gap-5">
            <div className="col-span-4 space-y-2">
              <Label>{t("workbench.products.modal.projectSpace")} {!isEdit && <span className="text-destructive">*</span>}</Label>
              {isEdit ? (
                <Input
                  readOnly
                  tabIndex={-1}
                  value={formState.projectSpace}
                  className="bg-muted/50 text-foreground cursor-default"
                />
              ) : (
                <Select value={formState.projectSpace} onValueChange={(v) => setFormState((prev) => ({ ...prev, projectSpace: v }))}>
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder={t("workbench.products.modal.projectSpacePlaceholder")} />
                  </SelectTrigger>
                  <SelectContent>
                    {projectSpaces.map((sp) => (
                      <SelectItem key={sp.value} value={sp.value}>
                        {sp.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
            </div>
            <div className="col-span-4 space-y-2">
              <Label>{t("workbench.products.modal.productVersion")} {!isEdit && <span className="text-destructive">*</span>}</Label>
              {isEdit ? (
                <Input
                  readOnly
                  tabIndex={-1}
                  value={formState.productVersion}
                  className="bg-muted/50 text-foreground cursor-default"
                />
              ) : (
                <Select value={formState.productVersion} onValueChange={handleVersionChange}>
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder={t("workbench.products.modal.productVersionPlaceholder")} />
                  </SelectTrigger>
                  <SelectContent>
                    {productVersions.map((v) => (
                      <SelectItem key={v.value} value={v.value}>
                        {v.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
            </div>
            <div className="col-span-4 space-y-2">
              <Label>
                {t("workbench.products.modal.appModule")} {!isEdit && <span className="text-destructive">*</span>}
              </Label>
              {isEdit ? (
                <Input
                  readOnly
                  tabIndex={-1}
                  value={formState.appModule}
                  className="bg-muted/50 text-foreground cursor-default"
                />
              ) : (
                <Select
                  value={formState.appModule}
                  onValueChange={handleModuleChange}
                  disabled={!formState.productVersion}
                >
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder={t("workbench.products.modal.appModulePlaceholder")} />
                  </SelectTrigger>
                  <SelectContent>
                    {appModules.map((m) => (
                      <SelectItem key={m.value} value={m.value}>
                        {m.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
              {!isEdit && formState.projectSpace === "space_1" && formState.productVersion === "v1.0.0" && (
                <div className="text-[11px] text-muted-foreground mt-1">{t("workbench.products.modal.moduleHint")}</div>
              )}
            </div>
          </div>

          <div className="space-y-2">
            <Label>{t("workbench.products.modal.description")} <span className="text-destructive">*</span></Label>
            <Textarea 
              rows={2} 
              placeholder={t("workbench.products.modal.descriptionPlaceholder")}
              value={formState.description}
              onChange={e => setFormState(prev => ({...prev, description: e.target.value}))}
              className="resize-none"
            />
          </div>

          <div className="space-y-2">
            <Label className="flex items-baseline justify-between">
              {t("workbench.products.modal.features")}
              <span className="text-[11px] font-normal text-muted-foreground">{t("workbench.products.modal.featuresExtra")}</span>
            </Label>
            <TagInput 
              value={formState.features} 
              onChange={v => setFormState(prev => ({...prev, features: v}))} 
              placeholderEmpty={t("workbench.products.modal.featuresInputPlaceholder")} 
            />
          </div>

          <div className="pt-4">
            <div className="flex items-center gap-2 mb-3">
              <GitBranch size={15} className="text-primary" />
              <span className="text-sm font-semibold">{t("workbench.products.modal.repoSection")}</span>
            </div>
            <div className="h-px bg-border/60 w-full mb-4" />

            {isEdit ? (
              <div className="space-y-3">
                <p className="text-xs text-muted-foreground">{t("workbench.products.modal.repoReadOnlyHint")}</p>
                {formState.repositories.length === 0 ? (
                  <div className="rounded-lg border border-dashed border-border/80 bg-muted/10 px-4 py-6 text-center text-sm text-muted-foreground">
                    {t("workbench.products.modal.repoReadOnlyEmpty")}
                  </div>
                ) : (
                  formState.repositories.map((repo, index) => (
                    <div
                      key={index}
                      className="rounded-lg border border-border/80 bg-muted/10 px-4 py-3 text-sm space-y-2"
                    >
                      <div className="flex items-center justify-between gap-2">
                        <span className="font-medium text-foreground">
                          {t("workbench.products.modal.repoConfigN", { n: index + 1 })}
                        </span>
                        {repo.isMain && (
                          <Badge variant="secondary" className="font-normal py-0 h-5 px-1.5 bg-blue-500/10 text-blue-700 dark:text-blue-400">
                            {t("workbench.products.modal.mainRepo")}
                          </Badge>
                        )}
                      </div>
                      <div className="grid gap-1.5 text-xs text-muted-foreground">
                        <div>
                          <span className="text-foreground/80">{t("workbench.products.modal.branch")}: </span>
                          {repo.branch || "—"}
                        </div>
                        <div className="break-all">
                          <span className="text-foreground/80">{t("workbench.products.modal.url")}: </span>
                          {repo.url || "—"}
                        </div>
                        <div>
                          <span className="text-foreground/80">{t("workbench.products.modal.purpose")}: </span>
                          {repo.purpose || "—"}
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            ) : !isProductInfoFilled ? (
              <div className="flex items-center justify-center p-8 rounded-lg border border-dashed border-border/80 bg-muted/20 text-sm text-muted-foreground">
                {t("workbench.products.modal.fillProductFirst")}
              </div>
            ) : (
              <div className="space-y-3">
                {formState.repositories.map((repo, index) => {
                  const idxStr = String(index);
                  const isExpanded = expandedRepos.includes(idxStr);
                  
                  return (
                    <div key={index} className="rounded-lg border border-border/80 bg-muted/10 overflow-hidden transition-all">
                      <div 
                        className="flex items-center justify-between px-4 py-3 cursor-pointer hover:bg-muted/30"
                        onClick={() => toggleRepoExpand(idxStr)}
                      >
                        <div className="flex items-center gap-2">
                          <ChevronRight size={14} className={`text-muted-foreground transition-transform ${isExpanded ? "rotate-90" : ""}`} />
                          <span className="text-sm font-medium text-foreground">
                            {t("workbench.products.modal.repoConfigN", { n: index + 1 })}
                          </span>
                          {repo.isMain && (
                            <Badge variant="secondary" className="ml-2 font-normal py-0 h-5 px-1.5 bg-blue-500/10 text-blue-700 dark:text-blue-400">
                              {t("workbench.products.modal.mainRepo")}
                            </Badge>
                          )}
                        </div>
                        <div className="text-xs text-muted-foreground truncate max-w-[200px]">
                          {repo.branch} · {repo.url || "未配置 URL"}
                        </div>
                      </div>
                      
                      {isExpanded && (
                        <div className="p-4 pt-1 border-t border-border/50 grid grid-cols-12 gap-4 bg-background/50">
                          <div className="col-span-4 space-y-2">
                            <Label className="text-xs">{t("workbench.products.modal.branch")} *</Label>
                            <Input className="h-8 text-xs" value={repo.branch} onChange={e => updateRepo(index, "branch", e.target.value)} placeholder={t("workbench.products.modal.branchPlaceholder")} />
                          </div>
                          <div className="col-span-8 space-y-2">
                            <Label className="text-xs">{t("workbench.products.modal.url")} *</Label>
                            <Input className="h-8 text-xs" value={repo.url} onChange={e => updateRepo(index, "url", e.target.value)} placeholder={t("workbench.products.modal.urlPlaceholder")} />
                          </div>
                          <div className="col-span-6 space-y-2">
                            <Label className="text-xs">{t("workbench.products.modal.purpose")} *</Label>
                            <Input className="h-8 text-xs" value={repo.purpose} onChange={e => updateRepo(index, "purpose", e.target.value)} placeholder={t("workbench.products.modal.purposePlaceholder")} />
                          </div>
                          <div className="col-span-6 space-y-2">
                            <Label className="text-xs">{t("workbench.products.modal.token")}</Label>
                            <Input className="h-8 text-xs" type="password" value={repo.token || ""} onChange={e => updateRepo(index, "token", e.target.value)} placeholder={t("workbench.products.modal.tokenPlaceholder")} />
                          </div>
                          <div className="col-span-12 flex items-center justify-between pt-2">
                            <div className="flex items-center gap-2">
                              <Switch checked={repo.isMain} onCheckedChange={c => updateRepo(index, "isMain", c)} id={`repo-main-${index}`} />
                              <Label htmlFor={`repo-main-${index}`} className="text-xs cursor-pointer">{t("workbench.products.modal.mainRepo")}</Label>
                            </div>
                            <Button variant="ghost" size="sm" onClick={() => removeRepo(index)} className="h-8 text-destructive hover:text-destructive hover:bg-destructive/10">
                              <Trash2 size={13} className="mr-1.5" />
                              {t("workbench.products.modal.removeRepo")}
                            </Button>
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}
                <Button 
                  variant="outline" 
                  className="w-full h-10 border-dashed bg-transparent hover:bg-muted/30"
                  onClick={addRepo}
                >
                  <GitBranch size={14} className="mr-2" />
                  {t("workbench.products.modal.addRepo")}
                </Button>
              </div>
            )}
          </div>
        </div>

        <DialogFooter className="px-6 py-4 border-t border-border/60 bg-muted/10">
          <Button variant="outline" onClick={onCancel}>{t("workbench.products.modal.cancel")}</Button>
          <Button onClick={() => void handleSubmit()}>{isEdit ? t("workbench.products.modal.update") : t("workbench.products.modal.create")}</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// TagInput component for product features
interface TagInputProps {
  value?: string[];
  onChange?: (value: string[]) => void;
  placeholderEmpty?: string;
}

function TagInput({ value = [], onChange, placeholderEmpty = "" }: TagInputProps) {
  const [inputVal, setInputVal] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      const trimmed = inputVal.trim();
      if (trimmed && !value.includes(trimmed)) {
        onChange?.([...value, trimmed]);
      }
      setInputVal("");
    } else if (e.key === 'Backspace' && !inputVal && value.length > 0) {
      onChange?.(value.slice(0, -1));
    }
  };

  const handleRemove = (tag: string) => {
    onChange?.(value.filter((x) => x !== tag));
  };

  return (
    <div
      className="flex flex-wrap items-center gap-1.5 p-1.5 min-h-[36px] border border-input bg-background rounded-md text-sm ring-offset-background focus-within:ring-2 focus-within:ring-ring focus-within:ring-offset-2 transition-colors cursor-text"
      onClick={() => inputRef.current?.focus()}
    >
      {value.map((tag) => (
        <Badge
          key={tag}
          variant="secondary"
          className="flex items-center gap-1 font-normal hover:bg-secondary/80 pr-1 h-6"
        >
          {tag}
          <div 
            className="flex items-center justify-center rounded-full hover:bg-muted/50 p-0.5 cursor-pointer"
            onClick={(e) => { e.stopPropagation(); handleRemove(tag); }}
          >
            <X size={10} />
          </div>
        </Badge>
      ))}
      <input
        ref={inputRef}
        value={inputVal}
        onChange={e => setInputVal(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={value.length === 0 ? placeholderEmpty : ""}
        className="flex-1 min-w-[120px] bg-transparent outline-none border-none focus:ring-0 placeholder:text-muted-foreground text-sm py-0.5 px-1"
      />
    </div>
  );
}