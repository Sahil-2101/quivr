"use client";
import Image from "next/image";
import { useEffect, useRef, useState } from "react";

import Icon from "@/lib/components/ui/Icon/Icon";
import { MinimalBrainForUser } from "@/lib/context/BrainProvider/types";
import { useUserSettingsContext } from "@/lib/context/UserSettingsProvider/hooks/useUserSettingsContext";
import { useAddedKnowledge } from "@/lib/hooks/useAddedKnowledge";
import { isUploadedKnowledge, Knowledge } from "@/lib/types/Knowledge";

import styles from "./BrainFolder.module.scss";
import KnowledgeItem from "./KnowledgeItem/KnowledgeItem";

type BrainFolderProps = {
  brain: MinimalBrainForUser;
  searchValue: string;
};

const BrainFolder = ({ brain, searchValue }: BrainFolderProps): JSX.Element => {
  const { isDarkMode } = useUserSettingsContext();
  const { allKnowledge } = useAddedKnowledge({
    brainId: brain.id,
  });
  const [folded, setFolded] = useState<boolean>(true);
  const contentRef = useRef<HTMLDivElement>(null);
  const [storedKnowledge, setStoredKnowledge] = useState<Knowledge[]>([]);

  const filteredKnowledge = storedKnowledge
    .filter((knowledge) =>
      isUploadedKnowledge(knowledge)
        ? knowledge.fileName.toLowerCase().includes(searchValue.toLowerCase())
        : knowledge.url.toLowerCase().includes(searchValue.toLowerCase())
    )
    .sort((a, b) => {
      const nameA = isUploadedKnowledge(a) ? a.fileName : a.url;
      const nameB = isUploadedKnowledge(b) ? b.fileName : b.url;

      return nameA.localeCompare(nameB);
    });

  const getContentHeight = (): string => {
    return folded ? "0" : `${contentRef.current?.scrollHeight}px`;
  };

  useEffect(() => {
    setStoredKnowledge([...allKnowledge]);
  }, [allKnowledge, storedKnowledge.length, searchValue]);

  return (
    <div className={styles.brain_folder_wrapper}>
      <div
        className={styles.brain_folder_header}
        onClick={() => setFolded(!folded)}
      >
        <div className={styles.left}>
          <Icon
            size="small"
            name="chevronDown"
            color="black"
            classname={`${styles.icon_rotate} ${
              folded ? styles.icon_rotate_down : styles.icon_rotate_right
            }`}
          />
          <Image
            className={isDarkMode ? styles.dark_image : ""}
            src={
              brain.integration_logo_url
                ? brain.integration_logo_url
                : "/default_brain_image.png"
            }
            alt="logo_image"
            width={18}
            height={18}
          />
          <span className={styles.name}>{brain.name}</span>
        </div>
      </div>
      <div
        ref={contentRef}
        className={`${styles.content_wrapper} ${
          folded ? styles.content_collapsed : styles.content_expanded
        }`}
        style={{ maxHeight: getContentHeight() }}
      >
        {filteredKnowledge.map((knowledge) => (
          <div key={knowledge.id} className={styles.knowledge}>
            <KnowledgeItem knowledge={knowledge} />
          </div>
        ))}
      </div>
    </div>
  );
};

export default BrainFolder;