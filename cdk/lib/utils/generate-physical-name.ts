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
  } = options ?? {};
  const hash = objectToHash(destroyCreate);
  if (maxLength < (prefix + hash + separator).length) {
    throw new Error("The prefix is longer than the maximum length.");
  }
  const uniqueName = cdk.Names.uniqueResourceName(scope, {
    maxLength: maxLength - (prefix + hash + separator).length,
    separator,
    allowedSpecialCharacters,
  });
  const name = `${prefix}${hash}${separator}${uniqueName}`;
  if (name.length > maxLength) {
    throw new Error(
      `The generated name is longer than the maximum length of ${maxLength}`
    );
  }
  return lower ? name.toLowerCase() : name;
}
