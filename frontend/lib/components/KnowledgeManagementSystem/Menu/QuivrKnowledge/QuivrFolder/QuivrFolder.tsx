import { useEffect, useState } from "react";

import { useKnowledgeApi } from "@/lib/api/knowledge/useKnowledgeApi";
import { KMSElement } from "@/lib/api/sync/types";
import { useKnowledgeContext } from "@/lib/components/KnowledgeManagementSystem/KnowledgeProvider/hooks/useKnowledgeContext";
import { Icon } from "@/lib/components/ui/Icon/Icon";
import { LoaderIcon } from "@/lib/components/ui/LoaderIcon/LoaderIcon";
import { handleDragOver, handleDrop } from "@/lib/helpers/kms";

import styles from "./QuivrFolder.module.scss";

interface QuivrFolderProps {
  element: KMSElement;
}

const QuivrFolder = ({ element }: QuivrFolderProps): JSX.Element => {
  const [folded, setFolded] = useState(true);
  const [loading, setLoading] = useState(false);
  const [isDraggedOver, setIsDraggedOver] = useState(false);
  const { getFiles } = useKnowledgeApi();
  const [kmsElements, setKMSElements] = useState<KMSElement[]>();
  const [selectedFolder, setSelectedFolder] = useState<boolean>(false);

  const {
    currentFolder,
    setCurrentFolder,
    setExploringQuivr,
    setExploredProvider,
    setRefetchFolderMenu,
  } = useKnowledgeContext();
  const { patchKnowledge } = useKnowledgeApi();

  useEffect(() => {
    setSelectedFolder(currentFolder?.id === element.id);
    if (currentFolder?.source === "local") {
      setExploringQuivr(true);
      setExploredProvider(undefined);
    }
  }, [currentFolder]);

  useEffect(() => {
    if (!folded) {
      setLoading(true);
      void (async () => {
        try {
          const res = await getFiles(element.id);
          setKMSElements(res);
          setLoading(false);
        } catch (error) {
          console.error("Failed to get sync files:", error);
          setLoading(false);
        }
      })();
    }
  }, [folded]);

  return (
    <div
      className={`${styles.folder_wrapper} ${
        !kmsElements?.filter((file) => file.is_folder).length && !loading
          ? styles.empty
          : ""
      } ${isDraggedOver ? styles.dragged : ""}`}
      onDrop={
        element.is_folder
          ? (event) =>
              void handleDrop({
                event,
                targetElement: element,
                patchKnowledge,
                setRefetchFolderMenu,
                currentFolder,
              })
          : undefined
      }
      onDragOver={(event) => {
        if (element.is_folder) {
          handleDragOver(event);
          setIsDraggedOver(true);
        }
      }}
      onDragLeave={() => setIsDraggedOver(false)}
    >
      <div className={styles.folder_line_wrapper}>
        <Icon
          name={folded ? "chevronRight" : "chevronDown"}
          size="normal"
          color="dark-grey"
          handleHover={true}
          onClick={() => setFolded(!folded)}
        />
        <span
          className={`${styles.name} ${selectedFolder ? styles.selected : ""}`}
          onClick={() => {
            setCurrentFolder({
              ...element,
              parentKMSElement: element.parentKMSElement,
            });
          }}
        >
          {element.file_name?.includes(".")
            ? element.file_name.split(".").slice(0, -1).join(".")
            : element.file_name}
        </span>
      </div>
      {!folded &&
        (loading ? (
          <div className={styles.loader_icon}>
            <LoaderIcon color="primary" size="small" />
          </div>
        ) : (
          <div className={styles.kms_elements_wrapper}>
            {kmsElements
              ?.filter((file) => file.is_folder)
              .map((folder, id) => (
                <div key={id}>
                  <QuivrFolder
                    element={{
                      ...folder,
                      parentKMSElement: element,
                    }}
                  />
                </div>
              ))}
          </div>
        ))}
    </div>
  );
};

export default QuivrFolder;