from networksecurity.entity.artifact_entity import DataIngestionArtifact
from networksecurity.entity.config_entity import DataValidationConfig
from networksecurity.constant.training_pipeline import SCHEMA_FILE_PATH
from networksecurity.exceptions.exception import NetworkSecurityException
from networksecurity.logging.logger import logging
from scipy.stats import ks_2samp
import pandas as pd
import os,sys
from networksecurity.utils.main_utils.utils import read_yaml_file,write_yaml_file
from networksecurity.entity.artifact_entity import DataValidationArtifact

class DataValidation:
    def __init__(self,data_ingestion_artifact:DataIngestionArtifact,
                 data_validation_config:DataValidationConfig):

        try:
            self.data_ingestion_artifact=data_ingestion_artifact
            self.data_validation_config=data_validation_config
            self._schema_config = read_yaml_file(SCHEMA_FILE_PATH)
        except Exception as e:
            raise NetworkSecurityException(e,sys)

    @staticmethod
    def read_data(file_path)->pd.DataFrame:
        try:
            return pd.read_csv(file_path)
        except Exception as e:
            raise NetworkSecurityException(e,sys)

    def validate_number_of_columns(self,dataframe:pd.DataFrame)->bool:
        try:
            number_of_columns = len(self._schema_config["columns"])
            logging.info(f"required no of columns : {number_of_columns}")
            logging.info(f"data frame of ha columns:{len(dataframe.columns)}")

            if len(dataframe.columns) == number_of_columns:
                return True
            else:
                return False
        except Exception as e:
            raise NetworkSecurityException(e,sys)

    def is_numerical_column_exist(self,dataframe: pd.DataFrame,numerical_columns: list) -> bool:
        try:

            dataframe_columns = dataframe.columns.tolist()

            missing_numerical_columns = []

            for column in numerical_columns:

                if column not in dataframe_columns:
                    missing_numerical_columns.append(column)

            if len(missing_numerical_columns) > 0:

                logging.info(
                    f"Missing numerical columns: "
                    f"{missing_numerical_columns}"
                )

                return False

            return True

        except Exception as e:
            raise NetworkSecurityException(e, sys)

    def detect_dataset_drift(self,base_df,current_df,threshold=0.05)->bool:
        try:
            status=True
            report={}
            for column in base_df.columns:
                d1=base_df[column]
                d2=current_df[column]
                is_same_dist=ks_2samp(d1,d2)
                if threshold<=is_same_dist.pvalue:
                    is_found=False
                else:
                    is_found=True
                    status=False
                report.update({column:{
                    "p_value":float(is_same_dist.pvalue),
                    "drift_status":is_found

                    }})
            drift_report_file_path = self.data_validation_config.drift_report_file_path

            #Create directory
            dir_path = os.path.dirname(drift_report_file_path)
            os.makedirs(dir_path,exist_ok=True)
            write_yaml_file(file_path=drift_report_file_path,content=report)
            return status

        except Exception as e:
            raise NetworkSecurityException(e,sys)


    def initated_data_validation(self)->DataValidationArtifact:
        try:
            train_file_path = self.data_ingestion_artifact.trained_file_path
            test_file_path = self.data_ingestion_artifact.test_file_path

            ##read  the data from train and test file
            train_dataframe = DataValidation.read_data(train_file_path)
            test_dataframe = DataValidation.read_data(test_file_path)

            #validate number of columns
            train_column_status=self.validate_number_of_columns(dataframe=train_dataframe)
            if not train_column_status:
                error_message = (
                    "Train Dataframe does not contain all columns\n"
                )

                raise NetworkSecurityException(
                    error_message,
                    sys
                )

            test_column_status=self.validate_number_of_columns(dataframe=test_dataframe)
            if not test_column_status:
                error_message = (
                    "Test Dataframe does not contain all columns\n"
                )

                raise NetworkSecurityException(
                    error_message,
                    sys
                )

            #get numerical columns exist
            numerical_columns = (self._schema_config["numerical_columns"])

            #check the numerical train dataframe
            train_numerical_status = self.is_numerical_column_exist(
            dataframe=train_dataframe,
            numerical_columns=numerical_columns
            )

            if not train_numerical_status:
                error_message = (
                    "Train dataframe does not contain all required numerical columns."
                )

                raise NetworkSecurityException(
                    error_message,
                    sys
                )

            # check the  numerical test dataframe
            test_numerical_status = self.is_numerical_column_exist(
                    dataframe=test_dataframe,
                    numerical_columns=numerical_columns
                )

            if not test_numerical_status:
                error_message = (
                    "Test dataframe does not contain all required numerical columns."
                )

                raise NetworkSecurityException(
                    error_message,
                    sys
                )

            logging.info(
                    "Numerical column validation completed successfully."
                )

            # detect the dataset drift

            drift_status=self.detect_dataset_drift(base_df=train_dataframe,current_df=test_dataframe)
            dir_path=os.path.dirname(self.data_validation_config.valid_train_file_path)
            os.makedirs(dir_path,exist_ok=True)

            train_dataframe.to_csv(
                    self.data_validation_config.valid_train_file_path, index=False, header=True

                )

            test_dataframe.to_csv(
                    self.data_validation_config.valid_test_file_path, index=False, header=True
                )
            # data validation artifact
            data_validation_artifact = DataValidationArtifact(
                validation_status=(
                    train_column_status
                    and test_column_status
                    and train_numerical_status
                    and test_numerical_status
                    and drift_status
                ),
                valid_train_file_path=(
                    self.data_validation_config.valid_train_file_path
                ),

                valid_test_file_path=(
                    self.data_validation_config.valid_test_file_path
                ),
                invalid_train_file_path=None,
                invalid_test_file_path=None,
                drift_report_file_path=self.data_validation_config.drift_report_file_path,
            )


            logging.info(
                f"Data validation artifact: "
                f"{data_validation_artifact}"
            )

            return data_validation_artifact

        except Exception as e:
            raise NetworkSecurityException(e,sys)

