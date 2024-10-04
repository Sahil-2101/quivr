"use client";

import { KMSElement } from "@/lib/api/sync/types";
import { Icon } from "@/lib/components/ui/Icon/Icon";
import { transformConnectionLabel } from "@/lib/helpers/providers";

import styles from "./FolderExplorerHeader.module.scss";

import { useKnowledgeContext } from "../../../KnowledgeProvider/hooks/useKnowledgeContext";

interface QuivrHeaderProps {
  currentFolder: KMSElement | undefined;
  loadRoot: () => void;
}

const QuivrHeader = ({ currentFolder, loadRoot }: QuivrHeaderProps) => (
  <>
    <span
      className={`${styles.name} ${currentFolder ? styles.hoverable : ""}`}
      onClick={() => void loadRoot()}
    >
      Quivr
    </span>
    {currentFolder && <Icon name="chevronRight" size="normal" color="black" />}
  </>
);

interface ProviderHeaderProps {
  currentFolder: KMSElement | undefined;
  loadRoot: () => void;
  exploredProvider: { provider: string };
}

const ProviderHeader = ({
  currentFolder,
  exploredProvider,
  loadRoot,
}: ProviderHeaderProps) => (
  <div className={`${styles.name} ${currentFolder ? styles.hoverable : ""}`}>
    <span onClick={() => loadRoot()}>
      {transformConnectionLabel(exploredProvider.provider)}
    </span>
    {currentFolder && <Icon name="chevronRight" size="normal" color="black" />}
  </div>
);

interface ParentFolderHeaderProps {
  currentFolder: KMSElement;
  loadParentFolder: () => void;
}

const ParentFolderHeader = ({
  currentFolder,
  loadParentFolder,
}: ParentFolderHeaderProps) => (
  <div className={styles.parent_folder}>
    <span className={styles.name} onClick={() => void loadParentFolder()}>
      {currentFolder.parentKMSElement?.file_name?.replace(/(\..+)$/, "")}
    </span>
    <Icon name="chevronRight" size="normal" color="black" />
  </div>
);

interface CurrentFolderHeaderProps {
  currentFolder: KMSElement | undefined;
  exploringQuivr: boolean;
}

const CurrentFolderHeader = ({
  currentFolder,
  exploringQuivr,
}: CurrentFolderHeaderProps) => (
  <div className={styles.current_folder}>
    {currentFolder?.icon && (
      <div className={styles.icon}>{currentFolder.icon}</div>
    )}
    <span
      className={`${styles.name} ${
        currentFolder?.parentKMSElement || (exploringQuivr && currentFolder)
          ? styles.selected
          : ""
      }`}
    >
      {currentFolder?.file_name?.replace(/(\..+)$/, "")}
    </span>
  </div>
);

const FolderExplorerHeader = (): JSX.Element => {
  const { currentFolder, setCurrentFolder, exploringQuivr, exploredProvider } =
    useKnowledgeContext();

  const loadParentFolder = () => {
    if (currentFolder?.parentKMSElement) {
      setCurrentFolder({
        ...currentFolder.parentKMSElement,
        parentKMSElement: currentFolder.parentKMSElement.parentKMSElement,
      });
    }
  };

  const loadRoot = () => {
    setCurrentFolder(undefined);
  };

  return (
    <div className={styles.header_wrapper}>
      {exploringQuivr && !currentFolder?.parentKMSElement ? (
        <QuivrHeader currentFolder={currentFolder} loadRoot={loadRoot} />
      ) : exploredProvider && !currentFolder?.parentKMSElement ? (
        <ProviderHeader
          currentFolder={currentFolder}
          exploredProvider={exploredProvider}
          loadRoot={loadRoot}
        />
      ) : (
        currentFolder?.parentKMSElement && (
          <ParentFolderHeader
            currentFolder={currentFolder}
            loadParentFolder={loadParentFolder}
          />
        )
      )}
      <CurrentFolderHeader
        currentFolder={currentFolder}
        exploringQuivr={exploringQuivr}
      />
    </div>
  );
};

export default FolderExplorerHeader;