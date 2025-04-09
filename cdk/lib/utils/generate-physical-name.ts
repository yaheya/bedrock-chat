/**
 * Reference: https://github.com/awslabs/generative-ai-cdk-constructs/blob/main/src/common/helpers/utils.ts
 */
import { IConstruct } from "constructs";
import * as cdk from "aws-cdk-lib";
import { createHash } from "crypto";

export interface GeneratePhysicalNameOptions
  extends cdk.UniqueResourceNameOptions {
  /**
   * Whether to convert the name to lower case.
   *
   * @default false
   */
  lower?: boolean;

  /**
   * This object is hashed for uniqueness and can force a destroy instead of a replace.
   * @default: undefined
   */
  destroyCreate?: any;

  /**
   * Whether to suppress truncation warnings.
   *
   * @default false
   */
  suppressWarnings?: boolean;

  /**
   * Minimum length to reserve for the unique part of the name.
   * Higher values ensure more uniqueness but may require more truncation of the prefix.
   *
   * @default 5
   */
  minUniqueNameLength?: number;
}

/**
 * Logs a warning message to the console
 */
function logWarning(message: string, suppressWarnings = false): void {
  if (!suppressWarnings) {
    console.warn(`\x1b[33mWARNING: ${message}\x1b[0m`);
  }
}

export function generatePhysicalName(
  /**
   * The CDK scope of the resource.
   */
  scope: IConstruct,
  /**
   * The prefix for the name.
   */
  prefix: string,
  /**
   * Options for generating the name.
   */
  options?: GeneratePhysicalNameOptions
): string {
  function objectToHash(obj: any): string {
    // Nothing to hash if undefined
    if (obj === undefined) {
      return "";
    }

    // Convert the object to a JSON string
    const jsonString = JSON.stringify(obj);

    // Create a SHA-256 hash
    const hash = createHash("sha256");

    // Update the hash with the JSON string and get the digest in hexadecimal format
    // Shorten it (modeled after seven characters like git commit hash shortening)
    return hash.update(jsonString).digest("hex").slice(0, 7);
  }

  const {
    maxLength = 256,
    lower = false,
    separator = "",
    allowedSpecialCharacters = undefined,
    destroyCreate = undefined,
    suppressWarnings = false,
    minUniqueNameLength = 5,
  } = options ?? {};

  const hash = objectToHash(destroyCreate);

  // Handle case where prefix is too long
  let truncatedPrefix = prefix;
  const minHashLength = hash.length;
  const minSeparatorLength = separator.length;
  // Use the configurable minUniqueNameLength instead of hardcoded value
  const totalMinLength =
    minHashLength + minSeparatorLength + minUniqueNameLength;

  if (truncatedPrefix.length + totalMinLength > maxLength) {
    const originalLength = truncatedPrefix.length;
    // Ensure we have at least enough space for the minimum requirements
    truncatedPrefix = truncatedPrefix.substring(
      0,
      Math.max(1, maxLength - totalMinLength)
    );
    logWarning(
      `Prefix '${prefix}' (${originalLength} chars) exceeds maximum allowed length. ` +
        `Truncated to '${truncatedPrefix}' (${truncatedPrefix.length} chars).`,
      suppressWarnings
    );
  }

  // Calculate remaining length for the unique name
  const remainingLength = Math.max(
    minUniqueNameLength,
    maxLength - (truncatedPrefix.length + hash.length + separator.length)
  );

  // Generate unique name with the remaining length
  let uniqueName;
  try {
    uniqueName = cdk.Names.uniqueResourceName(scope, {
      maxLength: remainingLength,
      separator,
      allowedSpecialCharacters,
    });
  } catch (err) {
    // If uniqueResourceName fails, generate a simple hash-based fallback
    const fallbackHash = createHash("md5")
      .update(scope.node.path)
      .digest("hex")
      .substring(0, remainingLength);

    logWarning(
      `Failed to generate unique resource name. Using fallback hash instead.`,
      suppressWarnings
    );

    uniqueName = fallbackHash;
  }

  // Combine all parts
  let name = `${truncatedPrefix}${hash}${separator}${uniqueName}`;

  // Final check to ensure we're within maxLength
  if (name.length > maxLength) {
    const originalName = name;
    name = name.substring(0, maxLength);
    logWarning(
      `Generated name '${originalName}' (${originalName.length} chars) exceeds maximum length of ${maxLength}. ` +
        `Truncated to '${name}' (${name.length} chars).`,
      suppressWarnings
    );
  }

  return lower ? name.toLowerCase() : name;
}
