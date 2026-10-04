import React, { useRef } from "react";
import { Upload } from "lucide-react";
import { Button } from "../common/Button";

interface UploadButtonProps {
  onFilesSelected: (files: File[]) => void;
  disabled?: boolean;
}

export const UploadButton: React.FC<UploadButtonProps> = ({
  onFilesSelected,
  disabled,
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleClick = () => {
    if (fileInputRef.current) {
      fileInputRef.current.value = ""; // reset so same file can be re-selected
      fileInputRef.current.click();
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const fileList = Array.from(e.target.files);
      onFilesSelected(fileList);
    }
  };

  return (
    <>
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileChange}
        multiple
        style={{ display: "none" }}
        aria-hidden="true"
      />
      <Button
        variant="primary"
        leftIcon={<Upload size={16} />}
        onClick={handleClick}
        disabled={disabled}
      >
        Upload
      </Button>
    </>
  );
};
